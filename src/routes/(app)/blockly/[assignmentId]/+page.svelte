<script>
  import { page } from '$app/stores';
  import BlocklyEditor from '$lib/components/blockly/BlocklyEditor.svelte';

  $: assignmentId = $page.params.assignmentId;
</script>

<BlocklyEditor
  assignmentId={assignmentId}
  exerciseTitle="Exercice Blockly — Somme de deux nombres"
  description="Créez un programme qui calcule et affiche la somme de a=3 et b=5."
  hints={["Utilisez un bloc Variable pour stocker chaque nombre.", "Le bloc Addition se trouve dans la catégorie Math."]}
/>
