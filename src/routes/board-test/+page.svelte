<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import * as THREE from 'three';
  import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
  import ClassroomBackground from '$lib/components/classroom/ClassroomBackground.svelte';
  
  let container: HTMLDivElement;
  let scene: THREE.Scene;
  let camera: THREE.PerspectiveCamera;
  let renderer: THREE.WebGLRenderer;
  let controls: OrbitControls;
  let animationFrameId: number;
  let testMessage = "This is a test message on the board.\nSecond line of text.";
  let messageInput: HTMLTextAreaElement;
  let initialized = false;
  let viewType: 'front-view' | 'side-view' = 'front-view';
  let classroomModel: 'default' | 'alternative' = 'default';
  
  // Debug position controls
  let posX = 0;
  let posY = 1.65;
  let posZ = -4.0;
  let boardPosition = { x: posX, y: posY, z: posZ };
  
  onMount(() => {
    console.log("Component mounted, initializing Three.js");
    initThreeJs();
    
    // Clean up on component destruction
    return () => {
      if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
      }
      if (renderer) {
        renderer.dispose();
      }
      if (controls) {
        controls.dispose();
      }
      window.removeEventListener('resize', handleResize);
    };
  });
  
  function initThreeJs() {
    // Create scene
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x87CEEB); // Light blue sky color
    
    // Create camera
    camera = new THREE.PerspectiveCamera(
      70, 
      window.innerWidth / window.innerHeight, 
      0.1, 
      1000
    );
    
    // Create renderer
    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.shadowMap.enabled = true;
    
    // Add renderer to container
    container.appendChild(renderer.domElement);
    
    // Add orbit controls
    controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    
    // Set camera initial position
    updateCameraForView();
    
    // Add lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
    scene.add(ambientLight);
    
    const directionalLight = new THREE.DirectionalLight(0xffffff, 1.0);
    directionalLight.position.set(1, 2, 3);
    directionalLight.castShadow = true;
    scene.add(directionalLight);
    
    // Add visual origin marker
    const originGeometry = new THREE.SphereGeometry(0.1, 16, 16);
    const originMaterial = new THREE.MeshBasicMaterial({ color: 0xffff00 });
    const originMarker = new THREE.Mesh(originGeometry, originMaterial);
    originMarker.position.set(0, 0, 0);
    scene.add(originMarker);
    
    // Add axis helper for orientation
    const axisHelper = new THREE.AxesHelper(2);
    scene.add(axisHelper);
    
    // Handle window resize
    window.addEventListener('resize', handleResize);
    
    // Animation loop
    animate();
    
    console.log("Three.js scene initialized");
    initialized = true;
  }
  
  function updateCameraForView() {
    if (!camera) return;
    
    if (viewType === 'front-view') {
      camera.position.set(0, 1.6, 5);
      camera.lookAt(0, 1, 0);
    } else {
      // Side view
      camera.position.set(4, 1.6, 0);
      camera.lookAt(0, 1, 0);
    }
    
    if (controls) {
      controls.update();
    }
  }
  
  function handleResize() {
    if (camera && renderer) {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    }
  }
  
  function animate() {
    animationFrameId = requestAnimationFrame(animate);
    if (controls) controls.update();
    if (renderer && scene && camera) {
      renderer.render(scene, camera);
    }
  }
  
  function updateBoardText() {
    if (messageInput) {
      testMessage = messageInput.value;
      console.log("Updated board text to:", testMessage);
    }
  }
  
  function toggleView() {
    viewType = viewType === 'front-view' ? 'side-view' : 'front-view';
    classroomModel = viewType === 'front-view' ? 'default' : 'alternative';
    updateCameraForView();
    
    // Update position based on view type
    if (viewType === 'front-view') {
      posX = 0;
      posY = 1.65;
      posZ = -4.0;
    } else {
      posX = 3.0;
      posY = 1.65;
      posZ = 0;
    }
    
    updateBoardPosition();
    console.log("Switched to view:", viewType, "with model:", classroomModel);
  }
  
  function updateBoardPosition() {
    boardPosition = { x: posX, y: posY, z: posZ };
    console.log("Updated board position to:", boardPosition);
  }
  
  // Any change to position values should update the boardPosition object
  $: if (posX !== undefined && posY !== undefined && posZ !== undefined) {
    boardPosition = { x: posX, y: posY, z: posZ };
  }
</script>

<div class="board-test-container">
  <div bind:this={container} class="canvas-container"></div>
  
  <div class="controls-panel">
    <h2>Test Board Text</h2>
    <textarea 
      bind:this={messageInput}
      rows="5" 
      bind:value={testMessage}
      placeholder="Enter text to display on the board"
    ></textarea>
    
    <button on:click={updateBoardText}>Update Board Text</button>
    
    <div class="view-controls">
      <h3>View Controls</h3>
      <button on:click={toggleView} class="toggle-view">
        Switch to {viewType === 'front-view' ? 'Side View' : 'Front View'}
      </button>
      <p>Current view: <strong>{viewType}</strong></p>
      <p>Model: <strong>{classroomModel}</strong></p>
    </div>
    
    <div class="position-controls">
      <h3>Board Position</h3>
      <div class="position-group">
        <label>X: <input type="number" bind:value={posX} step="0.1" /></label>
        <label>Y: <input type="number" bind:value={posY} step="0.1" /></label>
        <label>Z: <input type="number" bind:value={posZ} step="0.1" /></label>
        <button on:click={updateBoardPosition} class="position-button">Update Position</button>
      </div>
      <p class="position-display">Current: ({boardPosition.x.toFixed(2)}, {boardPosition.y.toFixed(2)}, {boardPosition.z.toFixed(2)})</p>
    </div>
    
    <div class="status">
      {#if initialized}
        <p class="success">Scene initialized. You should see the board.</p>
      {:else}
        <p class="waiting">Waiting for scene initialization...</p>
      {/if}
    </div>
  </div>
  
  {#if scene && camera}
    <ClassroomBackground 
      {scene} 
      {camera}
      boardMessage={testMessage}
      classroomModel={classroomModel}
      customBoardPosition={boardPosition}
    />
  {/if}
</div>

<style>
  .board-test-container {
    position: relative;
    width: 100%;
    height: 100vh;
    overflow: hidden;
  }
  
  .canvas-container {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
  }
  
  .controls-panel {
    position: absolute;
    top: 20px;
    right: 20px;
    width: 320px;
    background-color: rgba(255, 255, 255, 0.9);
    padding: 15px;
    border-radius: 8px;
    z-index: 10;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.2);
    max-height: 90vh;
    overflow-y: auto;
  }
  
  textarea {
    width: 100%;
    margin: 10px 0;
    padding: 8px;
    border-radius: 4px;
    border: 1px solid #ccc;
  }
  
  button {
    background-color: #4CAF50;
    color: white;
    padding: 10px 15px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-weight: bold;
    margin-bottom: 10px;
    width: 100%;
  }
  
  button:hover {
    background-color: #45a049;
  }
  
  .view-controls, .position-controls {
    margin-top: 20px;
    padding: 10px;
    background-color: rgba(0, 0, 0, 0.05);
    border-radius: 4px;
    margin-bottom: 10px;
  }
  
  .toggle-view {
    background-color: #2196F3;
  }
  
  .toggle-view:hover {
    background-color: #0b7dda;
  }
  
  .position-group {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin-bottom: 10px;
  }
  
  .position-group label {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  
  .position-group input {
    width: 70px;
    padding: 4px;
    margin-left: 5px;
  }
  
  .position-button {
    grid-column: 1 / 3;
    background-color: #ff9800;
  }
  
  .position-button:hover {
    background-color: #e68a00;
  }
  
  .position-display {
    font-family: monospace;
    background-color: #f5f5f5;
    padding: 5px;
    border-radius: 4px;
    text-align: center;
  }
  
  .status {
    margin-top: 15px;
    padding: 10px;
    border-radius: 4px;
    background-color: rgba(0, 0, 0, 0.05);
  }
  
  .success {
    color: #4CAF50;
    font-weight: bold;
  }
  
  .waiting {
    color: #f39c12;
    font-weight: bold;
  }
  
  h3 {
    margin-top: 0;
    margin-bottom: 10px;
  }
  
  p {
    margin: 5px 0;
  }
</style> 