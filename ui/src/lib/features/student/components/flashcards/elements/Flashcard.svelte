<script>
  export let question = "";
  export let answer = "";
  export let box = 1;
  let isFlipped = false;
  
  function flip() {
    isFlipped = !isFlipped;
  }
</script>

<div class="flashcard-container" on:click={flip} role="button" tabindex="0" 
     on:keydown={(e) => e.key === 'Enter' && flip()}>
  <div class="flashcard" class:flipped={isFlipped}>
    <div class="face front">
      <div class="box-indicator">Niveau {box}/5</div>
      <div class="label">Question</div>
      <div class="content">{question}</div>
      <div class="hint">Cliquez pour voir la réponse</div>
    </div>
    <div class="face back">
      <div class="label">Réponse</div>
      <div class="content">{answer}</div>
    </div>
  </div>
</div>

<style>
  .flashcard-container {
    perspective: 1000px;
    width: 100%;
    max-width: 600px;
    height: 350px;
    margin: 2rem auto;
    cursor: pointer;
    outline: none;
  }
  
  .flashcard-container:focus {
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.3);
    border-radius: 16px;
  }
  
  .flashcard {
    position: relative;
    width: 100%;
    height: 100%;
    transition: transform 0.6s cubic-bezier(0.4, 0.0, 0.2, 1);
    transform-style: preserve-3d;
  }
  
  .flashcard.flipped {
    transform: rotateY(180deg);
  }
  
  .face {
    position: absolute;
    width: 100%;
    height: 100%;
    backface-visibility: hidden;
    -webkit-backface-visibility: hidden;
    border-radius: 16px;
    padding: 2rem;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    box-shadow: 0 10px 40px rgba(0,0,0,0.15);
  }
  
  .front {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
  }
  
  .back {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    color: white;
    transform: rotateY(180deg);
  }
  
  .box-indicator {
    position: absolute;
    top: 1rem;
    right: 1rem;
    background: rgba(255,255,255,0.2);
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
  }
  
  .label {
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 2px;
    opacity: 0.9;
    margin-bottom: 1rem;
    font-weight: 600;
  }
  
  .content {
    font-size: 1.4rem;
    text-align: center;
    line-height: 1.6;
    max-width: 90%;
  }
  
  .hint {
    position: absolute;
    bottom: 1rem;
    font-size: 0.8rem;
    opacity: 0.7;
  }
</style>
