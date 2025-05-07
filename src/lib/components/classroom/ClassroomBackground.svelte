<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import * as THREE from 'three';
  import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
  import { DRACOLoader } from 'three/examples/jsm/loaders/DRACOLoader.js';

  // Props
  export let classroomModel: 'default' | 'alternative' = 'default';
  export let scene: THREE.Scene | null = null;
  export let camera: THREE.PerspectiveCamera | null = null;

  // Variables
  let classroom: THREE.Group | null = null;
  
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





  onMount(async () => {
    if (scene) {
      await loadClassroom();
    }
  });

  onDestroy(() => {
    // Clean up resources
    if (classroom && scene) {
      scene.remove(classroom);
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
    
    // Set up DRACO loader for compressed models
    const dracoLoader = new DRACOLoader();
    dracoLoader.setDecoderPath('/static/draco/'); // Path to draco decoder
    
    // Initialize GLTF loader with DRACO
    const loader = new GLTFLoader();
    loader.setDRACOLoader(dracoLoader);
    
    const modelPath = `/static/classroom/classroom_${classroomModel}.glb`;

    try {
      // Remove existing classroom if present
      if (classroom && scene) {
        scene.remove(classroom);
        classroom = null;
      }

      console.log(`Loading classroom model: ${modelPath}`);
      
      const gltf = await new Promise<any>((resolve, reject) => {
        loader.load(
          modelPath,
          (gltf) => resolve(gltf),
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
    } finally {
      // Clean up DRACO loader
      dracoLoader.dispose();
    }
  }

  // Watch for changes to scene or model
  $: if (scene && classroomModel) {
    loadClassroom();
  }
  
  // Export function to get board position for avatar placement
  export function getBoardPosition() {
    return classroomModel === 'default' 
      ? { x: 0, y: 0.1, z: -3.5 } 
      : { x: 0, y: 0.1, z: -3.2 };
  }
</script>

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