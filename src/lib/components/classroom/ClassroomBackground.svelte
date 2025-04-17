<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import * as THREE from 'three';
  import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
  import { DRACOLoader } from 'three/examples/jsm/loaders/DRACOLoader.js';
  import { CSS3DRenderer } from 'three/examples/jsm/renderers/CSS3DRenderer.js';
  import BoardText from './BoardText.svelte';

  // Props
  export let classroomModel: 'default' | 'alternative' = 'default';
  export let scene: THREE.Scene | null = null;
  export let camera: THREE.PerspectiveCamera | null = null;
  export let boardMessage: string = "";
  export let customBoardPosition: { x: number, y: number, z: number } | null = null;

  // Variables
  let classroom: THREE.Group | null = null;
  let cssRenderer: CSS3DRenderer | null = null;
  let container: HTMLElement;
  
  // Constants for positioning the classroom
  const classroomPositions = {
    default: {
      position: [0.15, -0.75, -0.7], // Adjusted to match the image view
      rotation: [0, 0, 0],
      scale: 1.3 // Slightly larger scale
    },
    alternative: {
      position: [0.15, -0.75, -0.7], // Adjusted to match the image view
      rotation: [0, -Math.PI/8, 0], // Slight angle for better view
      scale: 0.6 // Larger scale
    }
  };
  
  // Camera positions that simulate a student sitting at a desk in the first row
  const cameraPositions = {
    default: {
      position: [0, 1.15, 2.6],   // Raised slightly and pushed back for desk to appear
      lookAt: [0, 1.4, 0]         // Slight upward tilt to center teacher/board
    },
    alternative: {
      position: [0.4, 1.1, 2.3],   // Slightly off-center to the right (like right-side desk)
      lookAt: [0, 1.4, 0]
    }
  };

  onMount(() => {
    if (scene && container) {
      // Initialize CSS3D renderer for HTML content
      cssRenderer = new CSS3DRenderer();
      cssRenderer.setSize(window.innerWidth, window.innerHeight);
      cssRenderer.domElement.style.position = 'absolute';
      cssRenderer.domElement.style.top = '0';
      cssRenderer.domElement.style.left = '0';
      cssRenderer.domElement.style.pointerEvents = 'none';
      cssRenderer.domElement.style.zIndex = '10'; // Increased z-index to ensure it's on top
      container.appendChild(cssRenderer.domElement);
      
      // Set up window resize handler
      const handleResize = () => {
        if (cssRenderer && camera) {
          cssRenderer.setSize(window.innerWidth, window.innerHeight);
        }
      };
      
      window.addEventListener('resize', handleResize);
      
      // Load classroom without awaiting
      loadClassroom();
      
      // Set up animation loop to render CSS3D content
      if (camera) {
        const animate = () => {
          requestAnimationFrame(animate);
          if (cssRenderer && scene && camera) {
            cssRenderer.render(scene, camera);
          }
        };
        animate();
      }
      
      return () => {
        window.removeEventListener('resize', handleResize);
      };
    }
  });

  onDestroy(() => {
    // Clean up resources
    if (classroom && scene) {
      scene.remove(classroom);
    }
    if (cssRenderer && container) {
      container.removeChild(cssRenderer.domElement);
    }
  });

  // Function to set camera to student perspective
  function setCameraToStudentView() {
    if (!camera) return;
    
    const cameraSettings = cameraPositions[classroomModel];
    
    // Position camera like a student sitting at a desk
    camera.position.set(
      cameraSettings.position[0],
      cameraSettings.position[1],
      cameraSettings.position[2]
    );
    
    // Look toward the board/teacher area
    camera.lookAt(
      cameraSettings.lookAt[0],
      cameraSettings.lookAt[1],
      cameraSettings.lookAt[2]
    );
  }

  async function loadClassroom() {
    if (!scene) return;
    
    try {
      console.log("Starting classroom load process");
      
      // Set up DRACO loader for compressed models
      const dracoLoader = new DRACOLoader();
      
      // Try to use the static draco folders if available, with fallback
      dracoLoader.setDecoderPath('/static/draco/');
      console.log("DracoLoader path set");
      
      // Initialize GLTF loader with DRACO
      const loader = new GLTFLoader();
      loader.setDRACOLoader(dracoLoader);
      
      const modelPath = `/static/classroom/classroom_${classroomModel}.glb`;
      console.log("Attempting to load model from:", modelPath);

      // Remove existing classroom if present
      if (classroom && scene) {
        scene.remove(classroom);
        classroom = null;
      }

      // Add a placeholder board (colored plane) until the model loads
      const boardGeometry = new THREE.PlaneGeometry(3, 1.5);
      const boardMaterial = new THREE.MeshBasicMaterial({ 
        color: 0x1a5e1a, 
        side: THREE.DoubleSide 
      });
      const tempBoard = new THREE.Mesh(boardGeometry, boardMaterial);
      const boardPos = getBoardPosition();
      tempBoard.position.set(boardPos.x, boardPos.y, boardPos.z);
      scene.add(tempBoard);
      
      const gltf = await new Promise<any>((resolve, reject) => {
        loader.load(
          modelPath,
          (gltf) => {
            scene.remove(tempBoard);
            resolve(gltf);
          },
          (xhr) => {
            console.log(`Classroom loading: ${(xhr.loaded / (xhr.total || 1)) * 100}% loaded`);
          },
          (error) => {
            console.error('Error loading classroom model:', error);
            reject(error);
          }
        );
      });

      classroom = gltf.scene;
      
      // Apply position, rotation and scale based on classroom type
      const settings = classroomPositions[classroomModel];
      
      // Set position
      if (classroom) {
        classroom.position.set(
          settings.position[0], 
          settings.position[1], 
          settings.position[2]
        );
        
        // Set rotation
        classroom.rotation.set(
          settings.rotation[0], 
          settings.rotation[1], 
          settings.rotation[2]
        );
        
        // Set scale - uniform scale for all axes
        classroom.scale.set(
          settings.scale,
          settings.scale,
          settings.scale
        );
        
        // Add to scene
        scene.add(classroom);
        console.log('Classroom added to scene successfully');
      }
      
      // Set camera to student view
      setCameraToStudentView();
      
    } catch (error) {
      console.error('Failed to load classroom model:', error);
      
      // Add a fallback classroom environment - just a green board and floor
      const boardGeometry = new THREE.PlaneGeometry(3, 1.5);
      const boardMaterial = new THREE.MeshBasicMaterial({ 
        color: 0x1a5e1a, 
        side: THREE.DoubleSide 
      });
      const board = new THREE.Mesh(boardGeometry, boardMaterial);
      const boardPos = getBoardPosition();
      board.position.set(boardPos.x, boardPos.y, boardPos.z);
      
      const floorGeometry = new THREE.PlaneGeometry(10, 10);
      const floorMaterial = new THREE.MeshBasicMaterial({ 
        color: 0xd2b48c,
        side: THREE.DoubleSide
      });
      const floor = new THREE.Mesh(floorGeometry, floorMaterial);
      floor.rotation.x = Math.PI / 2;
      floor.position.y = -0.5;
      
      classroom = new THREE.Group();
      classroom.add(board);
      classroom.add(floor);
      scene.add(classroom);
      
      console.log('Using fallback classroom environment');
      
    } finally {
      // Clean up DRACO loader
      // dracoLoader.dispose(); // This might be causing issues, comment it out
    }
  }

  // Watch for changes to scene or model
  $: if (scene && classroomModel) {
    loadClassroom();
  }
  
  // Export function to get board position for avatar placement
  export function getBoardPosition() {
    if (classroomModel === 'default') {
      // Front-facing classroom with large green board
      return { 
        x: 0.3, 
        y: 1.8, 
        z: -5 // Moved further back to align with the board surface
      };
    } else {
      // Alternative classroom model
      return { 
        x: 3.3, 
        y: 1.8, 
        z: -0.4 // Also moved back for side view
      };
    }
  }
  
  // Function to detect which classroom model or view is being displayed
  function detectClassroomModel() {
    // If we don't have access to the classroom model yet, use default
    if (!classroom) return 'default';
    
    // Try to detect based on classroom properties
    return classroomModel === 'alternative' ? 'side-view' : 'front-view';
  }
</script>

<div bind:this={container} class="classroom-container">
  <!-- The 3D scene will be rendered here -->
</div>

{#if scene}
  <BoardText 
    {scene} 
    {camera}
    message={boardMessage} 
    position={getBoardPosition()} 
    viewType={classroomModel === 'default' ? 'front-view' : 'side-view'}
  />
{/if}

<style>
  .classroom-container {
    position: relative;
    width: 100%;
    height: 100%;
  }
</style>

<script context="module" lang="ts">
  // Preload classroom models
  function preloadModel(path: string) {
    const dracoLoader = new DRACOLoader();
    dracoLoader.setDecoderPath('/static/draco/');
    
    const loader = new GLTFLoader();
    loader.setDRACOLoader(dracoLoader);
    
    loader.load(
      path,
      () => console.log(`Preloaded: ${path}`),
      (xhr) => {
        const percentComplete = Math.round((xhr.loaded / (xhr.total || 1)) * 100);
        if (percentComplete % 25 === 0) {
          console.log(`Preloading ${path}: ${percentComplete}%`);
        }
      },
      (error) => console.error(`Error preloading ${path}:`, error)
    );
  }
  
  // Preload both classroom models
  preloadModel('/static/classroom/classroom_default.glb');
  preloadModel('/static/classroom/classroom_alternative.glb');
</script> 