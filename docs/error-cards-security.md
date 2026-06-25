# Sécurité — Carte d'erreur instantanée

Audit et corrections de sécurité appliquées sur la fonctionnalité Error Cards.

---

## 1. Authentification & Contrôle d'accès

### JWT vérifié sur les 3 endpoints

Chaque route error-cards passe par `get_current_user` via `Depends()`.
Le token est extrait du header `Authorization: Bearer <token>` et validé
avec `settings.JWT_SECRET_KEY` avant toute logique métier.

```python
# gateway/http/dependencies.py
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    payload = decode(
        credentials.credentials,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )
```

| Endpoint | Auth |
|----------|------|
| `POST /supports/{support_id}/error-cards/analyze` | `Depends(get_current_user)` |
| `GET /supports/{support_id}/error-cards` | `Depends(get_current_user)` |
| `DELETE /supports/{support_id}/error-cards/{card_id}` | `Depends(get_current_user)` |

Un token absent, expiré ou invalide retourne immédiatement `401` avec
le message générique `"Invalid authentication credentials"`.

### Rôle student uniquement

L'accès est limité aux étudiants par la vérification de propriété du support :
le service contrôle que `support.user_id == current_user.id` avant toute
analyse ou lecture. Un utilisateur d'un autre rôle qui ne possède pas le support
reçoit un `404` (masque l'existence de la ressource).

---

## 2. Validation des entrées

### `Field()` sur `AnalyzeExchangeRequest`

Les champs du body sont contraints avec `Field()` de Pydantic.
FastAPI renvoie automatiquement `422 Unprocessable Entity` si une contrainte
n'est pas respectée, sans jamais atteindre la couche service.

```python
# gateway/http/routers/supports.py
class AnalyzeExchangeRequest(BaseModel):
    user_message: str     = Field(min_length=1, max_length=10000)
    assistant_message: str = Field(min_length=1, max_length=10000)
    model: str            = Field(min_length=1, max_length=200)
```

| Champ | Contrainte | Effet d'un dépassement |
|-------|-----------|----------------------|
| `user_message` | 1 – 10 000 caractères | `422` automatique |
| `assistant_message` | 1 – 10 000 caractères | `422` automatique |
| `model` | 1 – 200 caractères | `422` automatique |

### Troncature défensive dans le service

En complément de la validation Pydantic, le service tronque les messages
avant insertion en base pour éviter toute dérive en cas de contournement :

```python
# learning/supports/error_cards/service.py
source_user_message=user_message[:2000],
source_assistant_message=assistant_message[:2000],
concept=str(entry["concept"])[:200],
```

### Validation de `support_id` et `card_id`

- `support_id` : vérifié en base via `SupportRepository.get_by_id()` —
  une valeur inexistante lève `NotFoundError` → `404`.
- `card_id` : filtré en base sur `(card_id, user_id, support_id)` simultanément —
  une valeur incohérente retourne `False` → `404`.

---

## 3. Anti-IDOR

### DELETE vérifie `card_id + user_id + support_id`

Avant correction, le `support_id` de l'URL était ignoré lors de la suppression.
Un utilisateur pouvait supprimer sa propre fiche en utilisant n'importe quel
`support_id` dans l'URL. Le filtre est maintenant triple :

```python
# learning/supports/error_cards/repository.py
def get_for_user(
    self, card_id: str, user_id: str, support_id: str
) -> Optional[ErrorCard]:
    return (
        self.session.query(ErrorCard)
        .filter(
            ErrorCard.id == card_id,
            ErrorCard.user_id == user_id,
            ErrorCard.support_id == support_id,
        )
        .first()
    )
```

La suppression échoue (`404`) si l'une des trois conditions n'est pas satisfaite.

### Cascade de la correction IDOR

| Couche | Avant | Après |
|--------|-------|-------|
| `repository.delete_for_user` | filtre `card_id + user_id` | filtre `card_id + user_id + support_id` |
| `service.delete_card` | paramètres `card_id, user_id` | paramètres `card_id, user_id, support_id` |
| `router DELETE` | `svc.delete_card(card_id, user.id)` | `svc.delete_card(card_id, user.id, support_id)` |

### UUIDv4 comme identifiants

`id`, `support_id`, `card_id` sont des UUIDv4 générés côté serveur.
Ils sont non-séquentiels et non-prédictibles, ce qui rend l'énumération
par force brute non viable.

### IDOR sur la lecture (GET)

La liste est filtrée par `(support_id, user_id)` dans le repository :
un utilisateur ne voit que ses propres fiches, même en fournissant un
`support_id` qui appartient à un autre utilisateur (la réponse sera `[]`).

---

## 4. Gestion des erreurs

### Message générique pour l'authentification

Avant correction, un token JWT valide référençant un `user_id` supprimé
retournait `"User not found"`, révélant l'état interne de la base.

```python
# gateway/http/dependencies.py — après correction
if user is None:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
    )
```

### Codes HTTP utilisés

| Situation | Code | Message client |
|-----------|------|---------------|
| Token absent ou invalide | `401` | `Invalid authentication credentials` |
| Support inexistant ou non possédé | `404` | `Support not found` (via `NotFoundError`) |
| Fiche inexistante ou non possédée | `404` | `Error card not found` |
| Body invalide (Field contraintes) | `422` | Détail Pydantic automatique |
| Erreur LLM ou parsing | `200` | `{ "cards": [] }` — dégradé silencieux |

Le choix `404` (plutôt que `403`) pour les ressources non-possédées empêche
l'énumération : un attaquant ne peut pas distinguer "n'existe pas" de
"existe mais pas à toi".

---

## 5. Sécurité LLM

### Réponse LLM validée avant insertion

La réponse du modèle de langage n'est jamais insérée directement en base.
Elle passe par un pipeline de validation à chaque étape :

```python
# learning/supports/error_cards/service.py
# Étape 1 — extraction JSON tolérante (gère les fences markdown, prose parasite)
parsed = self._extract_json(content)
if not parsed:
    return []

# Étape 2 — vérification de la structure
raw_errors = parsed.get("errors", [])
if not isinstance(raw_errors, list) or not raw_errors:
    return []

# Étape 3 — validation de chaque entrée
required = ["concept", "error_description", "simple_explanation", "correct_example"]
for entry in raw_errors:
    if not isinstance(entry, dict):
        continue
    if not all(entry.get(f) for f in required):
        continue   # entrée incomplète ignorée
    # Étape 4 — troncature avant insertion
    card = self.repo.create(concept=str(entry["concept"])[:200], ...)
```

### Dégradé silencieux en cas d'erreur

Aucune exception LLM n'est propagée au client. En cas d'échec réseau,
de réponse non-parseable ou de timeout, le service retourne `{ "cards": [] }`.
L'erreur est loguée côté serveur uniquement.

```python
except httpx.HTTPError as exc:
    log.warning("LLM analysis call failed for support %s: %s", support_id, exc)
    return []
```

### Prompt system isolé

Le prompt pédagogique est une constante Python (`ANALYZER_SYSTEM_PROMPT`),
jamais interpolée avec des données utilisateur. Les messages étudiant et tuteur
sont injectés uniquement dans le rôle `user` du payload LLM, ce qui empêche
toute injection de prompt via le rôle `system`.

---

## 6. Ce qui reste à configurer en infrastructure

Ces mesures ne peuvent pas être implémentées dans le code applicatif
et doivent être configurées au niveau infrastructure (reverse proxy, déploiement).

### Rate limiting

Limiter les appels à `POST /error-cards/analyze` par utilisateur pour éviter
l'abus de ressources LLM et les coûts excessifs.

```nginx
# Exemple Nginx
limit_req_zone $binary_remote_addr zone=error_cards:10m rate=10r/m;

location ~ ^/supports/.*/error-cards/analyze {
    limit_req zone=error_cards burst=5 nodelay;
}
```

Valeur recommandée : **10 requêtes/minute par utilisateur**.

### CSP Headers

Ajouter des en-têtes Content-Security-Policy pour protéger le frontend
contre les injections XSS, notamment si du contenu LLM est rendu en HTML.

```
Content-Security-Policy: default-src 'self'; script-src 'self'; object-src 'none'
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
```

### Logs JSON structurés

Les logs applicatifs actuels utilisent `log.warning(...)` en format texte.
En production, configurer un formatter JSON pour faciliter l'ingestion
dans un SIEM (Datadog, ELK, etc.) et permettre la détection d'anomalies.

```python
# config logging JSON (à ajouter dans main.py ou config logging)
import logging
import json

class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "support_id": getattr(record, "support_id", None),
        })
```

Événements à monitorer en priorité :
- Taux d'erreurs `POST /error-cards/analyze` > 20 % sur 5 min
- Tentatives de suppression sur `card_id` inconnus (possible scan)
- Tokens JWT rejetés en rafale depuis une même IP

---

## Hors périmètre de cette contribution

Les points suivants relèvent de la sécurité globale du projet et ne font
pas partie du code de cette contribution. Ils doivent être pris en charge
au niveau du projet.

| Point | Responsabilité |
|-------|---------------|
| **Cookies HttpOnly pour les tokens** | Concerne toute l'authentification du projet — décision d'architecture globale, pas spécifique aux error cards |
| **Rate limiting Nginx** | À configurer sur le reverse proxy au niveau infrastructure |
| **CSP headers** | À configurer au niveau serveur en production (Nginx, Caddy ou équivalent) |
| **Logs JSON structurés** | À configurer au niveau infrastructure (formatter logging, pipeline SIEM)
