<script lang="ts">
  import { onMount, onDestroy, createEventDispatcher } from 'svelte';
  import * as THREE from 'three';
  import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
  import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
  import Spinner from '$lib/components/common/Spinner.svelte';
  import { settings } from '$lib/stores';

  // Props
  export let history = {}; // Chat history
  export let currentMessage = ''; // Current message to speak
  export let speaking = false; // Whether the avatar is speaking
  export let className = 'h-full flex pt-8'; // CSS classes

  // State variables
  let avatarContainer: HTMLDivElement;
  let scene: THREE.Scene;
  let camera: THREE.PerspectiveCamera;
  let renderer: THREE.WebGLRenderer;
  let controls: OrbitControls;
  let avatar: THREE.Object3D;
  let headMesh: any; // For accessing morph targets
  let bodyBones: {[key: string]: THREE.Bone} = {}; // For accessing body bones
  let handBones: {[key: string]: THREE.Bone} = {}; // For accessing hand bones
  let allBones: {[key: string]: THREE.Bone} = {}; // Store all bones
  let initialRotations: {[key: string]: {x: number, y: number, z: number}} = {}; // Store initial pose
  let animationFrameId: number;
  let loading = true;
  let speechSynthesis = window.speechSynthesis;
  let voices: SpeechSynthesisVoice[] = [];
  let isSpeaking = false;
  let currentViseme = 0;
  let visemeSequence: {viseme: string, duration: number}[] = [];
  let visemeTimer: number | null = null;
  let gestureTimer: number | null = null;
  let bodyMovementTimer: number | null = null;
  let currentSentimentScore = 0; // Track sentiment for gesture intensity
  let activeGesture: string | null = null;
  let debugMode = true; // Enable debug mode
  let clock = new THREE.Clock(); // Clock for tracking animation time
  
  // Animation settings
  const ANIMATION_SETTINGS = {
    // More noticeable but still natural movements
    headNodIntensity: 0.08,
    headShakeIntensity: 0.07,
    handGestureIntensity: 0.15,
    bodyMovementIntensity: 0.05,
    breathingIntensity: 0.008,
    // More variety in timing
    minGestureInterval: 1800,
    maxGestureInterval: 4000,
    // Animation speeds
    gestureSpeed: 0.9,
    // Emotional expression settings
    expressionIntensity: 0.7,
    expressionDuration: 1500
  };
  
  // Animation transition settings
  const CROSSFADE_DURATION = 0.5; // Duration in seconds for animation crossfading
  
  // Viseme to expression mapping (if model supports these morphs)
  const EXPRESSIONS = {
    smile: 'viseme_smile',
    frown: 'viseme_frown',
    surprise: 'viseme_O', // Reuse O viseme for surprise
    squint: 'viseme_CH' // Reuse CH viseme for squinting/thinking
  };
  
  // Animation mapping definitions for different animation types
  const ANIMATION_MAPPINGS = {
    facialExpressions: {
      0: "neutral",      // Neutral
      1: "smile",        // Smile
      2: "frown",        // Frown
      3: "raised_eyebrows", // Raised eyebrows
      4: "surprise",     // Surprise
      5: "wink",         // Wink
      6: "sad",          // Sad expression
      7: "angry",        // Angry expression
    },
    headMovements: {
      0: "no_move",      // No movement
      1: "nod_small",    // Small nod
      2: "shake",        // Shake left-right
      3: "tilt",         // Tilt left-right
      4: "look_down",    // Look down
      5: "look_up",      // Look up
      6: "turn_left",    // Turn left
      7: "turn_right",   // Turn right
    },
    handGestures: {
      0: "no_move",      // No hand movement
      1: "open_hand",    // Open hand
      2: "pointing",     // Pointing
      3: "wave",         // Wave
      4: "open_palm",    // Open palm gesture
      5: "thumbs_up",    // Thumbs up
      6: "fist",         // Fist
      7: "peace_sign",   // Peace sign
      8: "finger_snap",  // Finger snap
    },
    eyeMovements: {
      0: "no_move",      // No eye movement
      1: "look_up",      // Look up
      2: "look_down",    // Look down
      3: "look_left",    // Look left
      4: "look_right",   // Look right
      5: "blink",        // Blink
      6: "wide_open",    // Eyes wide open
      7: "squint",       // Squint
    },
    bodyPostures: {
      0: "neutral",      // Neutral stance
      1: "forward_lean", // Lean forward
      2: "lean_back",    // Lean back
      3: "shoulders_up", // Shoulders raised
      4: "rest_arms",    // Rest arms
      5: "hands_on_hips", // Hands on hips
      6: "sit",          // Sitting posture
      7: "stand",        // Standing posture
    },
    // New section for GLB animations by category
    glbAnimations: {
      // Map human-readable names to file paths
      expression: {
        "talking_neutral": "/backend/glb/expression/M_Talking_Variations_001.glb",
        "talking_happy": "/backend/glb/expression/M_Talking_Variations_002.glb",
        "talking_excited": "/backend/glb/expression/M_Talking_Variations_005.glb",
        "talking_thoughtful": "/backend/glb/expression/M_Talking_Variations_007.glb",
        "talking_concerned": "/backend/glb/expression/M_Talking_Variations_009.glb",
        "expression_smile": "/backend/glb/expression/M_Standing_Expressions_001.glb",
        "expression_sad": "/backend/glb/expression/M_Standing_Expressions_007.glb",
        "expression_surprise": "/backend/glb/expression/M_Standing_Expressions_010.glb",
        "expression_thinking": "/backend/glb/expression/M_Standing_Expressions_013.glb",
        "expression_angry": "/backend/glb/expression/M_Standing_Expressions_016.glb"
      },
      idle: {
        "idle_normal": "/backend/glb/idle/M_Standing_Idle_001.glb",
        "idle_shift_weight": "/backend/glb/idle/M_Standing_Idle_Variations_001.glb",
        "idle_look_around": "/backend/glb/idle/M_Standing_Idle_Variations_003.glb",
        "idle_default": "/backend/glb/idle/M_Standing_Idle_Variations_004.glb",
        "idle_stretch": "/backend/glb/idle/M_Standing_Idle_Variations_006.glb",
        "idle_impatient": "/backend/glb/idle/M_Standing_Idle_Variations_008.glb"
      },
      locomotion: {
        "walk_forward": "/backend/glb/locomotion/M_Walk_001.glb",
        "walk_backward": "/backend/glb/locomotion/M_Walk_Backwards_001.glb",
        "jog_forward": "/backend/glb/locomotion/M_Jog_001.glb",
        "run_forward": "/backend/glb/locomotion/M_Run_001.glb",
        "jump": "/backend/glb/locomotion/M_Walk_Jump_001.glb",
        "crouch": "/backend/glb/locomotion/M_Crouch_Walk_003.glb"
      },
      dance: {
        "dance_casual": "/backend/glb/dance/M_Dances_001.glb",
        "dance_energetic": "/backend/glb/dance/M_Dances_003.glb",
        "dance_rhythmic": "/backend/glb/dance/M_Dances_007.glb",
        "dance_silly": "/backend/glb/dance/M_Dances_009.glb"
      }
    }
  };
  
  const dispatch = createEventDispatcher();

  // Get the currently selected avatar ID from settings
  let selectedAvatarId = ($settings as any)?.selectedAvatarId || 'The Scholar';
  
  onMount(async () => {
    // Retrieve avatar selection from user settings, with fallback
    selectedAvatarId = ($settings as any)?.selectedAvatarId || 'The Scholar';
    
    console.log(`Using avatar: ${selectedAvatarId}`);
    
    // Init 3D scene, camera, and renderer
    await initThreeJs();
    
    // Set up speech synthesis
    speechSynthesis.onvoiceschanged = () => {
      voices = speechSynthesis.getVoices();
      console.log('Available voices:', voices);
    };

    // Browsers sometimes load voices asynchronously - try to get them right away
    // but also set up the onvoiceschanged handler above as a backup
    voices = speechSynthesis.getVoices();
  });

  onDestroy(() => {
    // Clean up resources
    if (animationFrameId) {
      cancelAnimationFrame(animationFrameId);
    }
    
    if (renderer) {
      renderer.dispose();
    }
    
    // Stop any ongoing speech
    if (speechSynthesis) {
      speechSynthesis.cancel();
    }
    
    // Clear viseme animation
    if (visemeTimer) {
      clearTimeout(visemeTimer);
    }
  });

  async function initThreeJs() {
    if (!avatarContainer) return;
    
    // Set up Three.js scene
    scene = new THREE.Scene();
    scene.background = null; // Transparent background for better UI integration

    // Use container dimensions for proper sizing
    const width = avatarContainer.clientWidth;
    const height = avatarContainer.clientHeight;

    // Initialize perspective camera at optimal distance for headshot view
    camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(0, 1.6, 2.2); // Position for head and shoulders framing

    // Configure renderer with transparency support
    renderer = new THREE.WebGLRenderer({ 
      antialias: true,
      alpha: true  // Enable transparency for UI integration
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.setClearColor(0x000000, 0); // Fully transparent background
    avatarContainer.appendChild(renderer.domElement);

    // Add lighting for realistic rendering
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
    scene.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0xffffff, 1.7);
    directionalLight.position.set(0.5, 2, 1);
    scene.add(directionalLight);

    // Add interactive camera controls
    controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.minDistance = 1;
    controls.maxDistance = 5;
    controls.target.set(0, 1.5, 0); // Focus on head height
    controls.update();

    // Load selected avatar model from static/avatar directory
    // This uses the ID from user preferences to load the appropriate GLB file
    const avatarPath = `/static/avatar/${selectedAvatarId}.glb`;
    console.log(`Loading avatar from: ${avatarPath}`);
    await loadAvatar(avatarPath);

    // Start rendering loop
    animate();

    // Handle window resizing for responsive display
    window.addEventListener('resize', handleResize);
  }

  async function loadAvatar(modelPath: string) {
    loading = true;
    const loader = new GLTFLoader();
    
    try {
      const gltf = await new Promise((resolve, reject) => {
        loader.load(
          modelPath,
          (gltf) => resolve(gltf),
          (xhr) => {
            console.log(`${(xhr.loaded / (xhr.total || 1)) * 100}% loaded`);
          },
          (error) => {
            console.error('Error loading GLTF model:', error);
            reject(error);
          }
        );
      });

      avatar = gltf.scene;
      scene.add(avatar);

      // Debug: log full scene structure to help diagnose bone issues
      if (debugMode) {
        console.log('Full avatar structure:', avatar);
        // Create a function to recursively print the hierarchy
        function logHierarchy(object, indent = 0) {
          const spaces = ' '.repeat(indent * 2);
          console.log(
            `${spaces}${object.name} (Type: ${object.type}${object.isBone ? ', Bone' : ''}${
              object.isMesh ? ', Mesh' : ''
            })`
          );
          object.children.forEach(child => logHierarchy(child, indent + 1));
        }
        console.log('--- Avatar Hierarchy ---');
        logHierarchy(avatar);
        console.log('--- End Hierarchy ---');
      }

      // Find head mesh with morph targets (for viseme animation)
      avatar.traverse((node) => {
        const mesh = node as THREE.Mesh;
        if (mesh.morphTargetDictionary && mesh.morphTargetInfluences) {
          // First check if it has viseme_sil
          if (mesh.morphTargetDictionary['viseme_sil'] !== undefined) {
            headMesh = mesh;
            console.log('Found head mesh with visemes:', mesh.morphTargetDictionary);
            
            // Check if model supports additional expressions
            const supportedExpressions = Object.values(EXPRESSIONS).filter(
              expr => mesh.morphTargetDictionary[expr] !== undefined
            );
            
            if (supportedExpressions.length > 0) {
              console.log('Model supports expressions:', supportedExpressions);
            }
          } 
          // If no viseme_sil, check if it has morph targets that might be visemes
          else if (Object.keys(mesh.morphTargetDictionary).some(k => 
            k.includes('viseme') || k.includes('mouth') || k.includes('lip') || 
            k.includes('jaw') || k.includes('face'))) {
            
            headMesh = mesh;
            console.log('Found potential head mesh with morphs:', mesh.morphTargetDictionary);
          }
          // If still no match but we don't have a head mesh yet, and this has morph targets
          // just use the first mesh with morph targets
          else if (!headMesh && Object.keys(mesh.morphTargetDictionary).length > 0) {
            headMesh = mesh;
            console.log('Using fallback mesh with morph targets:', mesh.morphTargetDictionary);
          }
        }
        
        // Find and store important bones for animation
        if (node.type === 'Bone') {
          const bone = node as THREE.Bone;
          const name = bone.name.toLowerCase();
          
          // Store ALL bones for reference
          allBones[bone.name] = bone;
          
          // Store initial rotations of all bones
          initialRotations[bone.name] = { 
            x: bone.rotation.x, 
            y: bone.rotation.y, 
            z: bone.rotation.z 
          };
          
          // More flexible bone detection - use more keywords and patterns
          
          // Store body bones (expanded set of keywords)
          if (name.includes('neck') || name.includes('head') || 
              name.includes('spine') || name.includes('chest') || 
              name.includes('torso') || name.includes('hips') ||
              name.includes('waist') || name.includes('back') ||
              name.includes('collar') || name.includes('upper') ||
              name.includes('body')) {
            bodyBones[bone.name] = bone;
          }
          
          // Store hand/arm bones (expanded set of keywords)
          if (name.includes('arm') || name.includes('shoulder') || 
              name.includes('hand') || name.includes('wrist') ||
              name.includes('finger') || name.includes('thumb') ||
              name.includes('elbow') || name.includes('forearm') ||
              name.includes('upperlimb') || name.includes('lowerlimb')) {
            handBones[bone.name] = bone;
          }
        }
      });

      // If we didn't find any specific body bones but have "all bones", try to infer
      if (Object.keys(bodyBones).length === 0 && Object.keys(allBones).length > 0) {
        console.log('Attempting to infer body bones from available bones');
        
        // If a bone is near the top of the hierarchy and isn't a hand/arm, it's likely a body bone
        const potentialBodyBones = Object.entries(allBones).filter(([name, bone]) => {
          const isArm = name.toLowerCase().includes('arm') || 
                       name.toLowerCase().includes('hand') || 
                       name.toLowerCase().includes('finger');
          const isLeg = name.toLowerCase().includes('leg') || 
                       name.toLowerCase().includes('foot') || 
                       name.toLowerCase().includes('toe');
          return !isArm && !isLeg;
        });
        
        if (potentialBodyBones.length > 0) {
          potentialBodyBones.forEach(([name, bone]) => {
            bodyBones[name] = bone;
          });
          console.log('Inferred body bones:', Object.keys(bodyBones));
        }
      }

      // Do the same for hand bones
      if (Object.keys(handBones).length === 0 && Object.keys(allBones).length > 0) {
        console.log('Attempting to infer hand/arm bones from available bones');
        
        // If it's not a body part and not a leg, it's likely an arm
        const potentialHandBones = Object.entries(allBones).filter(([name, bone]) => {
          const isLeg = name.toLowerCase().includes('leg') || 
                       name.toLowerCase().includes('foot') || 
                       name.toLowerCase().includes('toe');
          return !isLeg;
        });
        
        if (potentialHandBones.length > 0) {
          potentialHandBones.forEach(([name, bone]) => {
            handBones[name] = bone;
          });
          console.log('Inferred hand bones:', Object.keys(handBones));
        }
      }

      // Only attempt animation if we found bones
      if (Object.keys(bodyBones).length > 0) {
        console.log('Found body bones:', Object.keys(bodyBones));
      } else {
        console.log('No usable body bones found for animation');
      }
      
      if (Object.keys(handBones).length > 0) {
        console.log('Found hand bones:', Object.keys(handBones));
      } else {
        console.log('No usable hand bones found for animation');
      }

      // Fallback: if we have any bones at all, let's try to use them
      if (Object.keys(bodyBones).length === 0 && Object.keys(handBones).length === 0 && 
          Object.keys(allBones).length > 0) {
        console.log('Using fallback bone animation with all available bones:', Object.keys(allBones));
        
        // Assign some bones to use for basic animations
        // Use top level bones for body movement
        const topLevelBones = Object.values(allBones).filter(bone => 
          !bone.parent || bone.parent.type !== 'Bone');
        
        if (topLevelBones.length > 0) {
          topLevelBones.forEach(bone => {
            bodyBones[bone.name] = bone;
          });
          console.log('Using top level bones for body animation:', 
            topLevelBones.map(b => b.name));
        }
      }

      // Center avatar in frame
      const box = new THREE.Box3().setFromObject(avatar);
      const size = box.getSize(new THREE.Vector3());
      const center = box.getCenter(new THREE.Vector3());
      
      avatar.position.set(-center.x, -center.y + size.y/2, -center.z);
      loading = false;
      
      // Set a more natural default pose instead of T-pose
      setDefaultPose();
      
      // Load the default idle animation
      loadGlbAnimation(ANIMATION_MAPPINGS.glbAnimations.idle.idle_default);
      
      // Start enhanced idle animation with more variety
      startEnhancedIdleAnimation();
      
    } catch (error) {
      console.error('Error loading avatar:', error);
      loading = false;
    }
  }

  // Function to set a more natural default pose
  function setDefaultPose() {
    if (!avatar) return;
    console.log("Setting default pose - resetting all bones to default position");
    
    // First reset ALL bones to zero rotation for a clean slate
    avatar.traverse((bone) => {
      if (bone.type === "Bone") {
        // Skip certain bones that might be part of base posture
        if (!bone.name.toLowerCase().includes('hips') && 
            !bone.name.toLowerCase().includes('root')) {
          // Reset to zero rotation
          bone.rotation.set(0, 0, 0);
        }
      }
    });
    
    // Now apply specific poses to arms and hands for natural-looking pose
    
    // Get arm bones
    const leftArmBones = Object.values(handBones).filter(bone => 
      bone.name.toLowerCase().includes('left')
    );
    
    const rightArmBones = Object.values(handBones).filter(bone => 
      bone.name.toLowerCase().includes('right')
    );
    
    // Adjust left arm bones to hang straight down
    leftArmBones.forEach(bone => {
      const name = bone.name.toLowerCase();
      
      // Handle specific bones for a natural resting pose
      if (name.includes('shoulder')) {
        bone.rotation.z = -0.1; // Slightly away from body
      } else if (name.includes('upperarm') || name.includes('upper_arm')) {
        bone.rotation.z = -0.05; // Slightly forward
      } else if (name.includes('forearm') || name.includes('lower_arm')) {
        bone.rotation.x = 0;
        bone.rotation.y = 0;
        bone.rotation.z = 0;
      } else if (name.includes('hand') || name.includes('wrist')) {
        // Rotate wrist to natural position
        bone.rotation.x = 0;
        bone.rotation.y = 0;
        bone.rotation.z = 0;
      }
      
      // Store the new position as the initial rotation
      initialRotations[bone.name] = { 
        x: bone.rotation.x, 
        y: bone.rotation.y, 
        z: bone.rotation.z 
      };
    });
    
    // Adjust right arm bones to hang straight down (mirror of left)
    rightArmBones.forEach(bone => {
      const name = bone.name.toLowerCase();
      
      // Handle specific bones for a natural resting pose
      if (name.includes('shoulder')) {
        bone.rotation.z = 0.1; // Slightly away from body
      } else if (name.includes('upperarm') || name.includes('upper_arm')) {
        bone.rotation.z = 0.05; // Slightly forward
      } else if (name.includes('forearm') || name.includes('lower_arm')) {
        bone.rotation.x = 0;
        bone.rotation.y = 0;
        bone.rotation.z = 0;
      } else if (name.includes('hand') || name.includes('wrist')) {
        // Rotate wrist to natural position
        bone.rotation.x = 0;
        bone.rotation.y = 0;
        bone.rotation.z = 0;
      }
      
      // Store the new position as the initial rotation
      initialRotations[bone.name] = { 
        x: bone.rotation.x, 
        y: bone.rotation.y, 
        z: bone.rotation.z 
      };
    });
    
    // Ensure torso/spine and head are straight
    Object.values(bodyBones).forEach(bone => {
      const name = bone.name.toLowerCase();
      
      // Keep spine/torso completely upright
      if (name.includes('spine') || name.includes('torso')) {
        bone.rotation.x = 0;
        bone.rotation.y = 0;
        bone.rotation.z = 0;
        
        // Store the new position as the initial rotation
        initialRotations[bone.name] = { 
          x: bone.rotation.x, 
          y: bone.rotation.y, 
          z: bone.rotation.z 
        };
      }
      
      // Keep head/neck straight
      if (name.includes('head') || name.includes('neck')) {
        bone.rotation.x = 0;
        bone.rotation.y = 0;
        bone.rotation.z = 0;
        
        // Store the new position as the initial rotation
        initialRotations[bone.name] = { 
          x: bone.rotation.x, 
          y: bone.rotation.y, 
          z: bone.rotation.z 
        };
      }
    });
    
    console.log("Default pose set - all bones reset to default position");
  }

  function startEnhancedIdleAnimation() {
    // More varied idle animation
    if (Object.keys(bodyBones).length === 0 && Object.keys(allBones).length === 0) return;
    
    activeEnhancedIdle = true;
    
    const idleAnimation = () => {
      if (!avatar) return;
      
      // If we're currently playing a GLB animation, especially an idle one,
      // don't apply bone-based idle animations that might conflict with it
      if (isPlayingGlbAnimation) {
        console.log("AVATAR - Enhanced idle paused while GLB animation is playing");
        
        // Check back in a bit to see if we can resume enhanced idle
        enhancedIdleTimer = setTimeout(() => {
          if (avatar) {
            idleAnimation();
          }
        }, 500);
        return;
      }
      
      const time = Date.now() * 0.0005; // Base timing
      const fastTime = Date.now() * 0.001; // Faster cycle for some movements
      const slowTime = Date.now() * 0.0002; // Slower cycle for others
      
      // Only animate if not in a specific gesture
      if (!activeGesture) {
        // Subtle breathing - use bodyBones if available, otherwise use any available bones
        const bonesToAnimate = Object.keys(bodyBones).length > 0 ? 
          Object.values(bodyBones) : Object.values(allBones).slice(0, 5); // Limit to first 5 bones if using allBones
        
        bonesToAnimate.forEach(bone => {
          const name = bone.name.toLowerCase();
          const initialRot = initialRotations[bone.name] || { x: 0, y: 0, z: 0 };
          
          // Chest/spine breathing or any general bone movement
          if (name.includes('chest') || name.includes('spine') || 
              name.includes('torso') || Object.keys(bodyBones).length === 0) {
            bone.rotation.x = initialRot.x + Math.sin(time) * ANIMATION_SETTINGS.breathingIntensity;
          }
          
          // Very subtle head movement while idle
          if (name.includes('neck') || name.includes('head') || 
              Object.keys(bodyBones).length === 0) {
            // Combine different frequencies for more natural motion
            bone.rotation.x = initialRot.x + Math.sin(slowTime) * ANIMATION_SETTINGS.breathingIntensity * 0.7;
            bone.rotation.y = initialRot.y + Math.sin(time * 0.7) * ANIMATION_SETTINGS.breathingIntensity * 0.8;
          }
          
          // Extremely subtle shoulder movement
          if (name.includes('shoulder') || name.includes('clavicle') || 
              Object.keys(bodyBones).length === 0) {
            bone.rotation.z = initialRot.z + Math.sin(slowTime * 1.3) * ANIMATION_SETTINGS.breathingIntensity * 0.5;
          }
        });
        
        // Occasional random blinks or slight hand adjustments
        if (Math.random() < 0.002 && headMesh?.morphTargetDictionary) { // 0.2% chance per frame
          performBlink();
        }
        
        if (Math.random() < 0.001) { // 0.1% chance per frame
          performMicroMovement();
        }
      }
      
      // Schedule next frame if component is still mounted and enhanced idle is active
      if (avatar && activeEnhancedIdle) {
        enhancedIdleTimer = setTimeout(idleAnimation, 1000 / 30);
      }
    };
    
    // Start the idle animation
    idleAnimation();
  }
  
  // Function to stop enhanced idle animations
  function stopEnhancedIdleAnimation() {
    activeEnhancedIdle = false;
    
    if (enhancedIdleTimer) {
      clearTimeout(enhancedIdleTimer);
      enhancedIdleTimer = null;
    }
    
    console.log("AVATAR - Enhanced idle animation stopped");
  }
  
  function performBlink() {
    // Quick blink animation if model supports it
    if (headMesh?.morphTargetDictionary) {
      // Try different potential blink morph targets
      const blinkMorphNames = ['viseme_blink', 'blink', 'eyeBlink', 'eye_blink',
        'blinkLeft', 'blinkRight', 'eyesClosed'];
      
      let blinkIndex = -1;
      let blinkMorphName = '';
      
      // Find the first supported blink morph
      for (const morphName of blinkMorphNames) {
        if (headMesh.morphTargetDictionary[morphName] !== undefined) {
          blinkIndex = headMesh.morphTargetDictionary[morphName];
          blinkMorphName = morphName;
          break;
        }
      }
      
      // If no dedicated blink morph, try to use a closed mouth/eyes viseme as substitute
      if (blinkIndex === -1) {
        const closedMouthVisemes = ['viseme_PP', 'viseme_sil', 'viseme_B', 'viseme_M'];
        for (const morphName of closedMouthVisemes) {
          if (headMesh.morphTargetDictionary[morphName] !== undefined) {
            blinkIndex = headMesh.morphTargetDictionary[morphName];
            blinkMorphName = morphName;
            break;
          }
        }
      }
      
      // If we found a usable morph target
      if (blinkIndex !== -1) {
        console.log('Performing blink using morph:', blinkMorphName);
        const duration = 150; // Quick blink
        const startTime = Date.now();
        
        const animateBlink = () => {
          const elapsed = Date.now() - startTime;
          const progress = Math.min(1, elapsed / duration);
          
          // Bell curve for blink
          const blinkValue = Math.sin(progress * Math.PI) * 0.9;
          headMesh.morphTargetInfluences[blinkIndex] = blinkValue;
          
          if (progress < 1 && !isSpeaking) {
            requestAnimationFrame(animateBlink);
          } else {
            headMesh.morphTargetInfluences[blinkIndex] = 0;
          }
        };
        
        animateBlink();
      } else if (debugMode) {
        console.log('No suitable blink morph target found');
      }
    }
  }
  
  function performMicroMovement() {
    // Extremely subtle random adjustment to make avatar feel alive
    if ((Object.keys(bodyBones).length === 0 && Object.keys(allBones).length === 0) || activeGesture) return;
    
    // Don't perform micro movements if GLB animations are active
    if (isPlayingGlbAnimation) {
      console.log("AVATAR - Skipping micro movement because GLB animation is active");
      return;
    }
    
    // Determine bones to use
    const useBodyBones = Object.keys(bodyBones).length > 0;
    const useHandBones = Object.keys(handBones).length > 0;
    
    // Define categories based on available bones
    const categories = [];
    
    if (useBodyBones) {
      categories.push({ 
        bones: Object.values(bodyBones).filter(b => b.name.toLowerCase().includes('head')),
        axis: 'y',
        intensity: 0.003,
        duration: 800
      });
    } else if (Object.keys(allBones).length > 0) {
      // Use some top-level bones if no specific body bones are available
      const topBones = Object.values(allBones).slice(0, 2); // Just use first couple bones
      categories.push({ 
        bones: topBones,
        axis: 'y',
        intensity: 0.003,
        duration: 800
      });
    }
    
    if (useHandBones) {
      categories.push({ 
        bones: Object.values(handBones).filter(b => b.name.toLowerCase().includes('wrist')),
        axis: 'z',
        intensity: 0.004,
        duration: 700
      });
      
      categories.push({ 
        bones: Object.values(bodyBones).filter(b => b.name.toLowerCase().includes('shoulder')),
        axis: 'z',
        intensity: 0.003,
        duration: 1000
      });
    } else if (Object.keys(allBones).length > 0) {
      // Just use some random bones from all bones if we don't have specific hand bones
      const randomBones = Object.values(allBones).slice(2, 4); // Use a couple different bones
      categories.push({ 
        bones: randomBones,
        axis: 'z',
        intensity: 0.003,
        duration: 700
      });
    }
    
    // If we didn't find any bones to use, just exit
    if (categories.length === 0) return;
    
    // Choose random category
    const category = categories[Math.floor(Math.random() * categories.length)];
    if (category.bones.length === 0) return;
    
    // Choose random bone from category
    const bone = category.bones[Math.floor(Math.random() * category.bones.length)];
    const initialRot = initialRotations[bone.name] || { x: 0, y: 0, z: 0 };
    
    const startTime = Date.now();
    const duration = category.duration;
    let progress = 0;
    let microMovementActive = true;
    
    const animateMicroMovement = () => {
      // Cancel the animation if GLB animations have started or the component is no longer active
      if (isPlayingGlbAnimation || !avatar || !microMovementActive) {
        // Reset to initial position
        bone.rotation.x = initialRot.x;
        bone.rotation.y = initialRot.y;
        bone.rotation.z = initialRot.z;
        return;
      }
      
      const elapsed = Date.now() - startTime;
      progress = Math.min(1, elapsed / duration);
      
      // Smooth ease in and out
      const ease = t => t<.5 ? 2*t*t : -1+(4-2*t)*t;
      const easedProgress = ease(progress);
      
      // Apply tiny movement based on selected axis
      if (category.axis === 'x') {
        bone.rotation.x = initialRot.x + Math.sin(easedProgress * Math.PI) * category.intensity;
      } else if (category.axis === 'y') {
        bone.rotation.y = initialRot.y + Math.sin(easedProgress * Math.PI) * category.intensity;
      } else {
        bone.rotation.z = initialRot.z + Math.sin(easedProgress * Math.PI) * category.intensity;
      }
      
      if (progress < 1 && !activeGesture && !isPlayingGlbAnimation && microMovementActive) {
        requestAnimationFrame(animateMicroMovement);
      } else {
        // Reset to initial position
        bone.rotation.x = initialRot.x;
        bone.rotation.y = initialRot.y;
        bone.rotation.z = initialRot.z;
      }
    };
    
    // Start animation
    animateMicroMovement();
    
    // Safety cleanup - stop after maximum duration + buffer
    setTimeout(() => {
      microMovementActive = false;
    }, duration + 100);
  }

  // Add a more robust animation function for any model
  function animateGenericBones(type = 'nod', intensity = 0.15) {
    // Fallback animation that works with any bone structure
    if ((Object.keys(bodyBones).length === 0 && Object.keys(allBones).length === 0) || activeGesture) return false;
    
    // Don't start a new animation if speech has already ended
    if (!isSpeaking) {
      console.log(`AVATAR - Not starting ${type} animation because speech has ended`);
      return false;
    }
    
    // Determine which bones to use (body bones if available, otherwise top-level bones)
    let bonesToUse = [];
    if (Object.keys(bodyBones).length > 0) {
      // For body animations, prioritize head, neck, chest bones
      if (type === 'head' || type === 'nod' || type === 'shake') {
        bonesToUse = Object.values(bodyBones).filter(bone => 
          bone.name.toLowerCase().includes('head') || 
          bone.name.toLowerCase().includes('neck')
        );
      } else if (type === 'body' || type === 'lean') {
        bonesToUse = Object.values(bodyBones).filter(bone => 
          bone.name.toLowerCase().includes('spine') || 
          bone.name.toLowerCase().includes('chest') ||
          bone.name.toLowerCase().includes('torso')
        );
      } else if (type === 'shoulders') {
        bonesToUse = Object.values(bodyBones).filter(bone => 
          bone.name.toLowerCase().includes('shoulder') || 
          bone.name.toLowerCase().includes('clavicle')
        );
      }
    }
    
    // If we couldn't find specific bones, fall back to using top level bones
    if (bonesToUse.length === 0) {
      // Use first 1-3 bones as fallback
      bonesToUse = Object.values(allBones).length > 0 ? 
        Object.values(allBones).slice(0, 3) : [];
    }
    
    // If we still have no bones to use, exit
    if (bonesToUse.length === 0) return false;
    
    // Set active gesture flag
    activeGesture = type;
    console.log(`Animating generic ${type} using bones:`, bonesToUse.map(b => b.name));
    
    // Store initial rotations
    const initialPositions = {};
    bonesToUse.forEach(bone => {
      initialPositions[bone.name] = {
        x: bone.rotation.x,
        y: bone.rotation.y,
        z: bone.rotation.z
      };
    });
    
    // Animation parameters - shorter maximum duration to prevent animations from running too long
    const duration = Math.min(1200 / ANIMATION_SETTINGS.gestureSpeed, 1500);
    const startTime = Date.now();
    let progress = 0;
    
    // Animation function based on type
    const animateGesture = () => {
      // If speech has ended or a different gesture is active, stop this animation immediately
      if (!isSpeaking || activeGesture !== type) {
        // Restore all bones to initial position
        bonesToUse.forEach(bone => {
          const initial = initialPositions[bone.name] || initialRotations[bone.name] || { x: 0, y: 0, z: 0 };
          bone.rotation.set(initial.x, initial.y, initial.z);
        });
        if (activeGesture === type) {
          activeGesture = null; // Only reset if this gesture is still the active one
        }
        return;
      }
      
      const elapsed = Date.now() - startTime;
      progress = Math.min(1, elapsed / duration);
      
      // Smooth easing
      const ease = t => t<.5 ? 2*t*t : -1+(4-2*t)*t;
      const easedProgress = ease(progress);
      
      // Apply animation based on type
      bonesToUse.forEach(bone => {
        const initial = initialPositions[bone.name] || initialRotations[bone.name] || { x: 0, y: 0, z: 0 };
        
        if (type === 'nod' || type === 'head') {
          // Nodding motion - X axis rotation
          bone.rotation.x = initial.x + 
            Math.sin(easedProgress * Math.PI * 2) * intensity * ANIMATION_SETTINGS.headNodIntensity;
        } else if (type === 'shake') {
          // Head shake - Y axis rotation
          bone.rotation.y = initial.y + 
            Math.sin(easedProgress * Math.PI * 3) * intensity * ANIMATION_SETTINGS.headShakeIntensity;
        } else if (type === 'tilt') {
          // Head tilt - Z axis rotation
          bone.rotation.z = initial.z + 
            Math.sin(easedProgress * Math.PI) * intensity * ANIMATION_SETTINGS.headNodIntensity;
        } else if (type === 'lean_forward' || type === 'forward') {
          // Forward lean - X axis for spine
          bone.rotation.x = initial.x + 
            Math.sin(easedProgress * Math.PI) * intensity * ANIMATION_SETTINGS.bodyMovementIntensity * 2;
        } else if (type === 'lean_back' || type === 'back') {
          // Backward lean - negative X axis for spine
          bone.rotation.x = initial.x - 
            Math.sin(easedProgress * Math.PI) * intensity * ANIMATION_SETTINGS.bodyMovementIntensity * 2;
        } else if (type === 'shoulders' || type === 'shrug') {
          // Shoulder movement - Z axis rotation
          bone.rotation.z = initial.z + 
            Math.sin(easedProgress * Math.PI) * intensity * ANIMATION_SETTINGS.bodyMovementIntensity * 2;
        }
      });
      
      if (progress < 1 && isSpeaking && activeGesture === type) {
        requestAnimationFrame(animateGesture);
      } else {
        // Restore to initial position
        bonesToUse.forEach(bone => {
          const initial = initialPositions[bone.name] || initialRotations[bone.name] || { x: 0, y: 0, z: 0 };
          bone.rotation.set(initial.x, initial.y, initial.z);
        });
        if (activeGesture === type) {
          activeGesture = null; // Only reset if this gesture is still the active one
        }
      }
    };
    
    animateGesture();
    return true;
  }

  function animate() {
    animationFrameId = requestAnimationFrame(animate);
    
    // Update animation mixers
    const delta = clock.getDelta();
    updateAnimations(delta);
    
    // Update orbit controls
    if (controls) {
      controls.update();
    }
    
    // Render scene
    if (scene && camera && renderer) {
      renderer.render(scene, camera);
    }
  }

  function handleResize() {
    if (!avatarContainer || !camera || !renderer) return;
    
    const width = avatarContainer.clientWidth;
    const height = avatarContainer.clientHeight;
    
    // Update camera
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    
    // Update renderer
    renderer.setSize(width, height);
  }

  // Watch for changes in currentMessage prop to speak new messages
  $: if (currentMessage && speaking) {
    processAndSpeak(currentMessage);
  }

  // Process response with animation instructions and then speak
  function processAndSpeak(message) {
    try {
      console.log("AVATAR - Message received:", message);
      
      // Default to the original message
      let textToSpeak = message;
      let jsonParsed = false;
      
      // Check if message is a string
      if (typeof message === 'string') {
        // Check for the exact pattern we're seeing in the console: "***json" followed by JSON
        // Also handle variations like "```json" or just "json"
        const jsonMarkerPattern = /(```json|```|json|\*\*\*json)[\s\n]*([\s\S]*)/;
        const jsonMatch = message.match(jsonMarkerPattern);
        
        if (jsonMatch && jsonMatch[2]) {
          console.log("AVATAR - Detected JSON marker, extracting content");
          
          // Extract the content after the marker
          let jsonContent = jsonMatch[2].trim();
          
          // If there's a closing backtick, remove it and everything after
          if (jsonContent.includes('```')) {
            jsonContent = jsonContent.split('```')[0].trim();
          }
          
          // Find the actual JSON object (between { and })
          const objectMatch = jsonContent.match(/(\{[\s\S]*\})/);
          if (objectMatch) {
            jsonContent = objectMatch[1];
            console.log("AVATAR - Extracted JSON content:", jsonContent);
            
            try {
              const parsedMessage = JSON.parse(jsonContent);
              jsonParsed = true;
              
              // Debug the parsed message
              console.log("AVATAR - JSON parsed successfully:", parsedMessage);
              
              // If we have a response field, use that for speaking
              if (parsedMessage.response !== undefined) {
                textToSpeak = parsedMessage.response;
                console.log("AVATAR - Found response field:", textToSpeak);
                
                // Apply animations if present
                if (parsedMessage.animation) {
                  console.log("AVATAR - Applying animations:", parsedMessage.animation);
                  applyAnimations(parsedMessage.animation);
                }
                
                // Process GLB animations if present
                if (parsedMessage.glbAnimation) {
                  console.log("AVATAR - Processing GLB animations:", parsedMessage.glbAnimation);
                  processGlbAnimation(parsedMessage);
                }
                
                // Process GLB animation paths if present
                if (parsedMessage.glbAnimationPath) {
                  console.log("AVATAR - Processing GLB animation paths");
                  processGlbAnimationPath(parsedMessage);
                }
              } else {
                console.log("AVATAR - No response field in parsed JSON, using original message");
              }
            } catch (parseError) {
              console.error("AVATAR - Error parsing JSON content:", parseError);
              console.log("AVATAR - Problematic JSON content:", jsonContent);
            }
          } else {
            console.log("AVATAR - Could not find JSON object in extracted content");
          }
        }
        // Regular JSON check (if message is not prefixed with a JSON marker)
        else if (message.trim().startsWith('{') && message.trim().endsWith('}')) {
          try {
            const parsedMessage = JSON.parse(message);
            jsonParsed = true;
            
            // Debug the parsed message
            console.log("AVATAR - JSON parsed successfully:", parsedMessage);
            
            // If we have a response field, use that for speaking
            if (parsedMessage.response !== undefined) {
              textToSpeak = parsedMessage.response;
              console.log("AVATAR - Found response field:", textToSpeak);
              
              // Apply animations if present
              if (parsedMessage.animation) {
                console.log("AVATAR - Applying animations:", parsedMessage.animation);
                applyAnimations(parsedMessage.animation);
              }
              
              // Process GLB animations if present
              if (parsedMessage.glbAnimation) {
                console.log("AVATAR - Processing GLB animations:", parsedMessage.glbAnimation);
                processGlbAnimation(parsedMessage);
              }
              
              // Process GLB animation paths if present
              if (parsedMessage.glbAnimationPath) {
                console.log("AVATAR - Processing GLB animation paths");
                processGlbAnimationPath(parsedMessage);
              }
            } else {
              console.log("AVATAR - No response field in parsed JSON, using original message");
            }
          } catch (parseError) {
            console.error("AVATAR - Error parsing JSON:", parseError);
          }
        } else {
          console.log("AVATAR - Message doesn't appear to be JSON, using as-is");
        }
      } else {
        console.log("AVATAR - Message is not a string, type:", typeof message);
      }
      
      // Remove any remaining JSON markers or triple backticks from the text
      if (textToSpeak && typeof textToSpeak === 'string') {
        textToSpeak = textToSpeak.replace(/(\*\*\*json|```json|```|json)[\s\n]*/g, '');
        textToSpeak = textToSpeak.replace(/```$/g, '');
      }
      
      // Always try to speak something
      console.log("AVATAR - Final text to speak:", textToSpeak);
      
      // Handle empty or undefined message
      if (!textToSpeak) {
        console.log("AVATAR - Empty message, using fallback text");
        textToSpeak = "I'm ready to assist you";
      }
      
      // Speak the text - whether it's from the response field or original message
      speakText(textToSpeak);
      
      // Apply default animation for plain text if no JSON was parsed
      if (!jsonParsed) {
        setTimeout(() => {
          if (isSpeaking) {
            const randomAnimation = Math.floor(Math.random() * 5);
            const defaultAnimations = {
              facial_expression: randomAnimation % 2, // 0 or 1 (neutral or smile)
              head_movement: randomAnimation % 3,     // 0, 1, or 2
              hand_gesture: 1,                       // 1 = open hand
              eye_movement: 0,                       // 0 = no move
              body_posture: randomAnimation % 2      // 0 or 1
            };
            applyAnimations(defaultAnimations);
          }
        }, 100);
      }
    } catch (e) {
      // Global error handler for the entire function
      console.error("AVATAR - Critical error in processAndSpeak:", e);
      try {
        // Try to at least speak something
        speakText("I encountered an error processing that message");
      } catch (speakError) {
        console.error("AVATAR - Even speech failed:", speakError);
      }
    }
  }
  
  // Helper function to process GLB animations
  function processGlbAnimation(parsedMessage) {
    if (typeof parsedMessage.glbAnimation === 'string') {
      // Single animation specified by name
      const category = parsedMessage.glbAnimationCategory || "expression";
      const animationMap = ANIMATION_MAPPINGS.glbAnimations[category] || {};
      
      if (animationMap[parsedMessage.glbAnimation]) {
        loadGlbAnimation(animationMap[parsedMessage.glbAnimation]);
      }
    } else if (Array.isArray(parsedMessage.glbAnimation)) {
      // Multiple animations specified
      parsedMessage.glbAnimation.forEach(anim => {
        if (typeof anim === 'string') {
          // Simple animation name
          const category = parsedMessage.glbAnimationCategory || "expression";
          const animationMap = ANIMATION_MAPPINGS.glbAnimations[category] || {};
          
          if (animationMap[anim]) {
            loadGlbAnimation(animationMap[anim]);
          }
        } else if (typeof anim === 'object') {
          // Detailed animation specification
          const category = anim.category || "expression";
          const name = anim.name;
          const animationMap = ANIMATION_MAPPINGS.glbAnimations[category] || {};
          
          if (name && animationMap[name]) {
            loadGlbAnimation(animationMap[name], 
              anim.loop === false ? THREE.LoopOnce : THREE.LoopRepeat,
              anim.duration || 0);
          }
        }
      });
    }
  }
  
  // Helper function to process GLB animation paths
  function processGlbAnimationPath(parsedMessage) {
    if (typeof parsedMessage.glbAnimationPath === 'string') {
      // Single animation path
      loadGlbAnimation(parsedMessage.glbAnimationPath);
    } else if (Array.isArray(parsedMessage.glbAnimationPath)) {
      // Multiple animation paths
      parsedMessage.glbAnimationPath.forEach(path => {
        if (typeof path === 'string') {
          loadGlbAnimation(path);
        } else if (typeof path === 'object') {
          loadGlbAnimation(
            path.path, 
            path.loop === false ? THREE.LoopOnce : THREE.LoopRepeat,
            path.duration || 0
          );
        }
      });
    }
  }

  function speakText(text: string) {
    // Stop any ongoing speech
    speechSynthesis.cancel();
    
    // Reset animation
    resetVisemes();
    resetGestures();
    
    // Instead of stopping all animations, crossfade to the talking animation
    // The appropriate talking animation will be loaded by processGlbAnimation
    // We'll keep the default idle animation state for returning to later
    // Keep track of the state before speaking
    const previousAnimations = {...currentAnimationActions};
    
    // Create a new utterance
    const utterance = new SpeechSynthesisUtterance(text);
    
    // Choose a voice (preferably an English male voice)
    voices = speechSynthesis.getVoices();
    
    // First try to find an English male voice
    let preferredVoice = voices.find(voice => 
      voice.lang.includes('en') && 
      voice.name.toLowerCase().includes('male')
    );
    
    // If no specific male voice found, try any English voice
    if (!preferredVoice) {
      preferredVoice = voices.find(voice => 
        voice.lang.includes('en')
      );
    }
    
    // Fallback to any voice that sounds natural
    if (!preferredVoice) {
      preferredVoice = voices.find(voice => 
        voice.name.includes('Google') || voice.name.includes('Natural') || voice.name.includes('Premium')
      );
    }
    
    if (preferredVoice) {
      utterance.voice = preferredVoice;
      console.log('Selected voice:', preferredVoice.name, 'Language:', preferredVoice.lang);
    }
    
    // Set properties
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;
    
    // Create basic viseme sequence
    createVisemeSequence(text);
    
    // Analyze text for occasional gestures - keep this light
    analyzeTextForGestures(text);
    
    // Set up events
    utterance.onstart = () => {
      isSpeaking = true;
      animateMouth();
      
      // Only animate body if we have the bones and the text is long enough
      if ((Object.keys(bodyBones).length > 0 || Object.keys(allBones).length > 0) && text.length > 20) {
        scheduleOccasionalGestures();
      }
    };
    
    utterance.onend = () => {
      console.log("AVATAR - Speech ended, applying NO-T-POSE fix");
      isSpeaking = false;
      
      // Clear states
      activeGesture = null;
      
      // Reset all morph targets to zero immediately
      if (headMesh && headMesh.morphTargetInfluences) {
        for (let i = 0; i < headMesh.morphTargetInfluences.length; i++) {
          headMesh.morphTargetInfluences[i] = 0;
        }
      }
      
      // CRITICAL CHANGE: We'll preload the idle animation BEFORE stopping other animations
      try {
        // Get the default idle animation path
        const idlePath = ANIMATION_MAPPINGS.glbAnimations.idle.idle_default;
        const fullPath = idlePath.startsWith('/') ? idlePath : '/' + idlePath;
        
        // Create a preload function that loads the idle animation first
        const preloadDefaultAnim = () => {
          new GLTFLoader().load(fullPath, (gltf) => {
            if (gltf.animations && gltf.animations.length > 0) {
              console.log("Preloaded default idle animation, now stopping others");
              
              // Now we have the idle animation loaded, prepare the mixer
              if (!mainAnimationMixer) {
                mainAnimationMixer = new THREE.AnimationMixer(avatar);
                animationMixers = [mainAnimationMixer];
              }
              
              // Create the idle action but don't play it yet
              const idleAction = mainAnimationMixer.clipAction(gltf.animations[0]);
              idleAction.setLoop(THREE.LoopRepeat);
              idleAction.reset();
              
              // FORCE DIRECT BONE POSITIONS FOR ARMS - this prevents the t-pose
              // First ensure all arms and hands are in default pose
              Object.values(handBones).forEach(bone => {
                const name = bone.name.toLowerCase();
                
                if (name.includes('shoulder')) {
                  if (name.includes('left')) {
                    bone.rotation.z = -0.1; // Slightly away from body
                  } else {
                    bone.rotation.z = 0.1;  // Slightly away from body
                  }
                } else if (name.includes('upperarm') || name.includes('upper_arm')) {
                  if (name.includes('left')) {
                    bone.rotation.z = -0.05; // Slightly forward
                  } else {
                    bone.rotation.z = 0.05;  // Slightly forward
                  }
                } else if (name.includes('forearm') || name.includes('lower_arm') ||
                          name.includes('hand') || name.includes('wrist')) {
                  // Reset hand and lower arm positions
                  bone.rotation.set(0, 0, 0);
                }
              });
              
              // Reset body bones to default
              Object.values(bodyBones).forEach(bone => {
                const name = bone.name.toLowerCase();
                if (name.includes('spine') || name.includes('torso') || 
                   name.includes('head') || name.includes('neck')) {
                  bone.rotation.set(0, 0, 0);
                }
              });
              
              // NOW that arm positions are set correctly, stop all animations
              for (const mixer of animationMixers) {
                mixer.stopAllAction();
              }
              
              // Clear animation tracking
              currentAnimationActions = {};
              isPlayingGlbAnimation = false; // Ensure flags are reset properly 
              isPlayingIdleGlbAnimation = true; // This should be true for idle animation
              
              // Now play the idle animation
              idleAction.play();
              
              // Store as the only animation
              currentAnimationActions = {};
              currentAnimationActions[fullPath] = idleAction;
            }
          });
        };
        
        // Start the preload process
        preloadDefaultAnim();
      } catch (err) {
        console.error("Error transitioning to idle:", err);
        
        // Fallback to traditional transition if preload fails
        // First stop all animations
        for (const mixer of animationMixers) {
          mixer.stopAllAction();
        }
        
        // Set default pose
        setDefaultPose();
        
        // Load the default idle animation
        const idlePath = ANIMATION_MAPPINGS.glbAnimations.idle.idle_default;
        loadGlbAnimation(idlePath);
      }
      
      dispatch('speechend');
    };
    
    utterance.onerror = () => {
      console.log("AVATAR - Speech error, returning to default animation");
      isSpeaking = false;
      resetVisemes();
      resetGestures();
      
      // Crossfade back to the default animation instead of abruptly stopping everything
      fadeToDefaultState();
      
      dispatch('speechend');
    };
    
    // Speak the text
    speechSynthesis.speak(utterance);
  }

  function stopSpeaking() {
    if (isSpeaking) {
      speechSynthesis.cancel();
      isSpeaking = false;
      resetVisemes();
      resetGestures();
      
      // Crossfade back to the default animation instead of abruptly stopping
      fadeToDefaultState();
      
      dispatch('speechend');
    }
  }

  function createVisemeSequence(text: string) {
    // This is a more sophisticated approach for phoneme-to-viseme mapping
    visemeSequence = [];
    
    // Split text into words, punctuation, and handle spaces
    const words = text.match(/[\w']+|[.,!?;]|\s+/g) || [];
    
    // Map of common phoneme patterns to visemes
    const phonemeToViseme = {
      // Consonants
      'b': 'viseme_PP', 'm': 'viseme_PP', 'p': 'viseme_PP',
      'f': 'viseme_FF', 'v': 'viseme_FF',
      'th': 'viseme_TH',
      'd': 'viseme_DD', 't': 'viseme_DD', 'n': 'viseme_DD',
      'k': 'viseme_kk', 'g': 'viseme_kk',
      'ch': 'viseme_CH', 'j': 'viseme_CH', 'sh': 'viseme_CH',
      's': 'viseme_SS', 'z': 'viseme_SS',
      'l': 'viseme_nn', 'n': 'viseme_nn',
      'r': 'viseme_RR',
      // Vowels
      'a': 'viseme_aa', 'i': 'viseme_I', 'e': 'viseme_E',
      'o': 'viseme_O', 'u': 'viseme_U'
    };
    
    words.forEach(word => {
      // For punctuation, add a pause
      if (/[.,!?;]/.test(word)) {
        visemeSequence.push({ viseme: 'viseme_sil', duration: 200 });
        return;
      }
      
      // For spaces, add a brief pause
      if (/\s+/.test(word)) {
        visemeSequence.push({ viseme: 'viseme_sil', duration: 50 });
        return;
      }
      
      // Start with closed mouth
      visemeSequence.push({ viseme: 'viseme_sil', duration: 30 });
      
      // Estimate syllables (rough approximation)
      const syllables = word.toLowerCase().match(/[aeiouy]+/g) || [];
      const syllableCount = Math.max(syllables.length, 1);
      
      // Process each character/sound in the word to create a more natural sequence
      const chars = word.toLowerCase().split('');
      let i = 0;
      
      while (i < chars.length) {
        let viseme = 'viseme_sil';
        let duration = 60; // Base duration
        
        // Check for digraphs first (th, ch, sh)
        if (i < chars.length - 1) {
          const digraph = chars[i] + chars[i+1];
          if (phonemeToViseme[digraph]) {
            viseme = phonemeToViseme[digraph];
            i += 2;
            visemeSequence.push({ viseme, duration: duration * 1.5 });
            continue;
          }
        }
        
        // Single character processing
        if (phonemeToViseme[chars[i]]) {
          viseme = phonemeToViseme[chars[i]];
          
          // Vowels get longer duration
          if (/[aeiouy]/.test(chars[i])) {
            duration *= 2;
          }
        }
        
        visemeSequence.push({ viseme, duration });
        i++;
      }
      
      // End with closed mouth
      visemeSequence.push({ viseme: 'viseme_sil', duration: 30 });
    });
  }

  function animateMouth() {
    if (!isSpeaking || !headMesh || visemeSequence.length === 0) {
      resetVisemes();
      return;
    }
    
    // Get current viseme
    const currentVisemeObj = visemeSequence[0];
    
    // Apply viseme
    if (headMesh.morphTargetDictionary && headMesh.morphTargetInfluences) {
      // Reset all visemes
      Object.keys(headMesh.morphTargetDictionary).forEach(viseme => {
        if (viseme.startsWith('viseme_')) {
          const index = headMesh.morphTargetDictionary[viseme];
          headMesh.morphTargetInfluences[index] = 0;
        }
      });
      
      // Set current viseme
      if (headMesh.morphTargetDictionary[currentVisemeObj.viseme] !== undefined) {
        const index = headMesh.morphTargetDictionary[currentVisemeObj.viseme];
        headMesh.morphTargetInfluences[index] = 1.0;
      }
    }
    
    // Schedule next viseme
    visemeTimer = setTimeout(() => {
      // Remove the first viseme
      visemeSequence.shift();
      
      // Continue animation if there are more visemes
      if (visemeSequence.length > 0) {
        animateMouth();
      } else {
        resetVisemes();
      }
    }, currentVisemeObj.duration);
  }

  function resetVisemes() {
    // Clear any pending animation
    if (visemeTimer) {
      clearTimeout(visemeTimer);
      visemeTimer = null;
    }
    
    // Reset all visemes if we have the head mesh
    if (headMesh && headMesh.morphTargetDictionary && headMesh.morphTargetInfluences) {
      Object.keys(headMesh.morphTargetDictionary).forEach(viseme => {
        if (viseme.startsWith('viseme_')) {
          const index = headMesh.morphTargetDictionary[viseme];
          headMesh.morphTargetInfluences[index] = 0;
        }
      });
      
      // Set back to neutral/silent
      if (headMesh.morphTargetDictionary['viseme_sil'] !== undefined) {
        const index = headMesh.morphTargetDictionary['viseme_sil'];
        headMesh.morphTargetInfluences[index] = 1.0;
      }
    }
  }

  function resetGestures() {
    // Clear any pending gesture timers
    if (gestureTimer) {
      clearTimeout(gestureTimer);
      gestureTimer = null;
    }
    
    if (bodyMovementTimer) {
      clearTimeout(bodyMovementTimer);
      bodyMovementTimer = null;
    }
    
    // Reset active gesture flag
    activeGesture = null;
    
    // Cancel any ongoing animations by immediately stopping them
    if (animationFrameId) {
      cancelAnimationFrame(animationFrameId);
      // Restart the main render loop but not gesture animations
      animationFrameId = requestAnimationFrame(animate);
    }
    
    // Reset all bones to their initial position if we have them
    if (Object.keys(allBones).length > 0) {
      Object.entries(allBones).forEach(([name, bone]) => {
        const initialRot = initialRotations[name] || { x: 0, y: 0, z: 0 };
        bone.rotation.set(initialRot.x, initialRot.y, initialRot.z);
      });
    }
  }

  function analyzeTextForGestures(text: string) {
    // Enhanced text analysis with more nuanced emotion detection
    const hasQuestion = text.includes('?');
    const hasExclamation = text.includes('!');
    const wordCount = text.split(' ').length;
    
    // Extended sentiment analysis
    const positiveWords = ['great', 'good', 'excellent', 'happy', 'love', 'like', 'wonderful', 'amazing', 'fantastic', 'perfect', 'awesome'];
    const negativeWords = ['bad', 'terrible', 'hate', 'dislike', 'sad', 'unfortunate', 'awful', 'poor', 'horrible', 'wrong', 'upset'];
    const questionWords = ['what', 'how', 'why', 'when', 'where', 'who', 'which'];
    const emphasisWords = ['very', 'extremely', 'absolutely', 'definitely', 'certainly', 'never', 'always', 'must', 'should'];
    
    let sentiment = 0;
    let emphasis = 0;
    
    // More nuanced sentiment analysis
    positiveWords.forEach(word => {
      if (text.toLowerCase().includes(word)) sentiment += 0.15;
    });
    
    negativeWords.forEach(word => {
      if (text.toLowerCase().includes(word)) sentiment -= 0.15;
    });
    
    // Check for emphasis words
    emphasisWords.forEach(word => {
      if (text.toLowerCase().includes(word)) emphasis += 0.1;
    });
    
    // Add for punctuation
    if (hasExclamation) {
      sentiment += 0.15;
      emphasis += 0.15;
    }
    if (hasQuestion) emphasis += 0.1;
    
    // Limit to reasonable range
    currentSentimentScore = Math.max(-0.5, Math.min(0.5, sentiment));
    
    // Store emphasis for gesture intensity
    const emphasisScore = Math.max(0.1, Math.min(0.5, emphasis));
    
    // Look for specific emotions to trigger expressions
    let detectedEmotion = null;
    
    if (text.toLowerCase().includes('happy') || text.toLowerCase().includes('smile') || 
        text.toLowerCase().includes('glad') || text.toLowerCase().includes('joy')) {
      detectedEmotion = 'smile';
    } else if (text.toLowerCase().includes('sad') || text.toLowerCase().includes('sorry') || 
               text.toLowerCase().includes('unfortunate') || text.toLowerCase().includes('regret')) {
      detectedEmotion = 'frown';
    } else if (text.toLowerCase().includes('surprise') || text.toLowerCase().includes('wow') || 
               text.toLowerCase().includes('amazing') || text.toLowerCase().includes('incredible')) {
      detectedEmotion = 'surprise';
    } else if (text.toLowerCase().includes('think') || text.toLowerCase().includes('consider') || 
               text.toLowerCase().includes('perhaps') || text.toLowerCase().includes('maybe')) {
      detectedEmotion = 'squint';
    }
    
    // Possibly trigger expression
    if (detectedEmotion && Math.random() < 0.6 && headMesh) { // 60% chance
      performExpression(detectedEmotion);
    }
    
    // Log for debugging
    console.log('Speech analysis - Sentiment:', currentSentimentScore, 'Emphasis:', emphasisScore, 'Emotion:', detectedEmotion);
    
    return { sentiment: currentSentimentScore, emphasis: emphasisScore, emotion: detectedEmotion };
  }
  
  function scheduleOccasionalGestures() {
    if (!isSpeaking) return;
    
    // Calculate interval based on speech content
    const gestureInterval = ANIMATION_SETTINGS.minGestureInterval + 
                           Math.random() * (ANIMATION_SETTINGS.maxGestureInterval - ANIMATION_SETTINGS.minGestureInterval);
    
    // Schedule an occasional gesture
    gestureTimer = setTimeout(() => {
      // Double-check speech state to prevent late animations
      if (!isSpeaking) {
        console.log("AVATAR - Speech already stopped, canceling scheduled gesture");
        return;
      }
      
      // 50% chance of any gesture at all
      if (Math.random() > 0.5) {
        // Skip this opportunity
        scheduleOccasionalGestures();
        return;
      }
      
      // Choose a gesture based on randomness and sentiment influence
      const rand = Math.random();
      let gestureType = '';
      
      // Movement intensity based on sentiment
      const intensity = Math.abs(currentSentimentScore) * 0.2 + 0.15; // Range: 0.15-0.25
      
      // Different gestures based on sentiment
      if (currentSentimentScore > 0.2) {
        // Positive sentiment - more open/affirmative gestures
        if (rand < 0.25) {
          performHeadNod(intensity * 1.1);
          gestureType = 'head nod';
        } else if (rand < 0.5) {
          performExpressiveHandGesture('open', intensity);
          gestureType = 'open hand gesture';
        } else if (rand < 0.75) {
          performForwardLean(intensity);
          gestureType = 'forward lean';
        } else {
          animateGenericBones('tilt', intensity);
          gestureType = 'head tilt';
        }
      } else if (currentSentimentScore < -0.2) {
        // Negative sentiment - more closed/defensive gestures
        if (rand < 0.25) {
          performHeadShake(intensity);
          gestureType = 'head shake';
        } else if (rand < 0.5) {
          performExpressiveHandGesture('defensive', intensity);
          gestureType = 'defensive hand gesture';
        } else if (rand < 0.75) {
          performShoulderRaise(intensity);
          gestureType = 'shoulder raise';
        } else {
          animateGenericBones('lean_back', intensity);
          gestureType = 'weight shift';
        }
      } else {
        // Neutral sentiment - mixed gestures
        if (rand < 0.2) {
          performHeadNod(intensity * 0.9);
          gestureType = 'subtle head nod';
        } else if (rand < 0.4) {
          performExpressiveHandGesture('neutral', intensity * 0.9);
          gestureType = 'neutral hand gesture';
        } else if (rand < 0.6) {
          animateGenericBones('lean_back', intensity * 0.9);
          gestureType = 'subtle weight shift';
        } else if (rand < 0.8) {
          animateGenericBones('tilt', intensity * 0.9);
          gestureType = 'subtle head tilt';
        } else {
          performShoulderRaise(intensity * 0.9);
          gestureType = 'subtle shoulder adjustment';
        }
      }
      
      console.log('Performing gesture:', gestureType, 'with intensity:', intensity);
      
      // Schedule next gesture if still speaking, but with shorter max interval
      // This ensures we don't schedule gestures too far into the future
      if (isSpeaking) {
        // Use a shorter max interval for subsequent gestures
        ANIMATION_SETTINGS.maxGestureInterval = Math.min(ANIMATION_SETTINGS.maxGestureInterval, 3000);
        scheduleOccasionalGestures();
      }
    }, gestureInterval);
  }
  
  function performHandWave(intensity = 0.25) {
    if (Object.keys(handBones).length === 0) return false;
    
    // Don't start a new animation if speech has already ended
    if (!isSpeaking) {
      console.log("AVATAR - Not starting hand wave because speech has ended");
      return false;
    }
    
    const rightHandBones = Object.values(handBones).filter(bone => 
      bone.name.toLowerCase().includes('right')
    );
    
    if (rightHandBones.length === 0) return false;
    
    activeGesture = 'wave';
    
    const initialPositions = {};
    rightHandBones.forEach(bone => {
      initialPositions[bone.name] = {
        x: bone.rotation.x,
        y: bone.rotation.y,
        z: bone.rotation.z
      };
    });
    
    // Shorter maximum duration to prevent animations from running too long
    const duration = Math.min(1800 / ANIMATION_SETTINGS.gestureSpeed, 2000);
    const startTime = Date.now();
    let progress = 0;
    
    const animateWave = () => {
      // If speech has ended or a different gesture is active, stop this animation immediately
      if (!isSpeaking || activeGesture !== 'wave') {
        rightHandBones.forEach(bone => {
          const initial = initialPositions[bone.name] || initialRotations[bone.name] || { x: 0, y: 0, z: 0 };
          bone.rotation.set(initial.x, initial.y, initial.z);
        });
        if (activeGesture === 'wave') {
          activeGesture = null; // Only reset if this gesture is still the active one
        }
        return;
      }
      
      const elapsed = Date.now() - startTime;
      progress = Math.min(1, elapsed / duration);
      
      rightHandBones.forEach(bone => {
        const initial = initialPositions[bone.name] || initialRotations[bone.name] || { x: 0, y: 0, z: 0 };
        const name = bone.name.toLowerCase();
        
        if (name.includes('wrist') || name.includes('hand')) {
          // Waving motion
          bone.rotation.z = initial.z + 
            Math.sin(progress * Math.PI * 4) * intensity * ANIMATION_SETTINGS.handGestureIntensity * 1.5;
          bone.rotation.y = initial.y + 
            Math.sin(progress * Math.PI) * intensity * ANIMATION_SETTINGS.handGestureIntensity;
        } else if (name.includes('arm')) {
          bone.rotation.y = initial.y + 
            Math.sin(progress * Math.PI) * intensity * ANIMATION_SETTINGS.handGestureIntensity * 0.8;
        }
      });
      
      if (progress < 1 && isSpeaking && activeGesture === 'wave') {
        requestAnimationFrame(animateWave);
      } else {
        rightHandBones.forEach(bone => {
          const initial = initialPositions[bone.name] || initialRotations[bone.name] || { x: 0, y: 0, z: 0 };
          bone.rotation.set(initial.x, initial.y, initial.z);
        });
        if (activeGesture === 'wave') {
          activeGesture = null; // Only reset if this gesture is still the active one
        }
      }
    };
    
    animateWave();
    return true;
  }

  // Storage for animation mixers and actions
  let animationMixers = [];
  let currentAnimationActions = {};
  let mainAnimationMixer = null; // Single mixer for better transition control

  // Animation state tracking
  let isPlayingGlbAnimation = false; // Track if a GLB animation is currently playing
  let isPlayingIdleGlbAnimation = false; // Track if an idle GLB animation is playing
  let activeEnhancedIdle = false; // Track if enhanced idle is active
  let enhancedIdleTimer = null; // Timer for enhanced idle animations

  // Load and play a GLB animation
  function loadGlbAnimation(animationPath, loopType = THREE.LoopRepeat, duration = 0, crossfadeDuration = CROSSFADE_DURATION) {
    console.log(`Loading GLB animation: ${animationPath}`);
    
    // Skip if we're not ready to animate
    if (!avatar || !scene) {
      console.log("Avatar or scene not ready, skipping animation");
      return;
    }
    
    // Fix the path construction to ensure correct URL format
    // Always use absolute path from the site root
    const fullPath = animationPath.startsWith('/')
      ? animationPath  // Keep the leading slash for absolute paths
      : '/' + animationPath;  // Add leading slash for relative paths
    
    console.log(`Full animation path: ${fullPath}`);
    
    // Check if this is the default idle animation
    const isDefaultIdle = fullPath.includes('idle_default');
    
    // Special handling for default idle animation
    if (isDefaultIdle) {
      // First, ensure we stop all current animations 
      // This prevents any weird transitions
      for (const mixer of animationMixers) {
        mixer.stopAllAction();
      }
      
      // Clear all tracked animations
      currentAnimationActions = {};
    }
    
    // Check if this animation is already active (to avoid reloading it)
    if (currentAnimationActions[fullPath] && !isDefaultIdle) {
      console.log(`Animation ${fullPath} is already active, not reloading`);
      return;
    }
    
    try {
      // Load the animation file
      console.log("Loading glb animation file...");
      new GLTFLoader().load(fullPath, (gltf) => {
        console.log(`GLTF animation loaded: ${fullPath}`);
        
        if (gltf.animations && gltf.animations.length > 0) {
          console.log(`Found ${gltf.animations.length} animations in ${fullPath}`);
          
          // Create a main mixer if we don't have one yet
          if (!mainAnimationMixer) {
            mainAnimationMixer = new THREE.AnimationMixer(avatar);
            animationMixers.push(mainAnimationMixer);
          }
          
          // Use the first animation clip
          const clip = gltf.animations[0];
          console.log(`Using animation clip: ${clip.name}`);
          
          // Create an action for this animation
          const action = mainAnimationMixer.clipAction(clip);
          
          // Set up the action
          action.setLoop(loopType);
          action.clampWhenFinished = true;
          action.enabled = true;
          
          // Different handling for default idle vs. other animations
          if (isDefaultIdle) {
            // For default idle, just play immediately with no transition
            action.reset();
            action.setEffectiveTimeScale(1);
            action.setEffectiveWeight(1);
            action.play();
          } else {
            // For other animations, use crossfade
            fadeToNewAction(action, crossfadeDuration);
          }
          
          // Store the action for later reference
          currentAnimationActions[fullPath] = action;
          
          console.log(`Animation playing: ${fullPath}`);
        } else {
          console.warn(`No animations found in ${fullPath}`);
        }
      }, 
      // Progress callback
      (xhr) => {
        console.log(`${animationPath} ${(xhr.loaded / xhr.total * 100)}% loaded`);
      }, 
      // Error callback
      (error) => {
        console.error(`Error loading animation ${animationPath}:`, error);
      });
    } catch (error) {
      console.error(`Failed to load animation ${animationPath}:`, error);
    }
  }
  
  // Helper function to crossfade to a new animation
  function fadeToNewAction(newAction, duration = CROSSFADE_DURATION) {
    // Reduce the weight of all current animations
    Object.values(currentAnimationActions).forEach(action => {
      if (action !== newAction) {
        action.enabled = true;
        action.setEffectiveTimeScale(1);
        action.setEffectiveWeight(1);
        action.fadeOut(duration);
      }
    });
    
    // Fade in the new animation
    newAction.enabled = true;
    newAction.setEffectiveTimeScale(1);
    newAction.setEffectiveWeight(1);
    newAction.fadeIn(duration);
    newAction.play();
  }
  
  // Helper function to fade out a specific animation
  function fadeOutAction(action, duration = CROSSFADE_DURATION) {
    action.enabled = true;
    action.setEffectiveTimeScale(1);
    action.fadeOut(duration);
    
    // Stop the action after fade out duration
    setTimeout(() => {
      action.stop();
    }, duration * 1000);
  }

  // Update animations in the animation loop
  function updateAnimations(delta) {
    // Update all animation mixers
    for (const mixer of animationMixers) {
      mixer.update(delta);
    }
  }

  // Add this new function to stop all GLB animations
  function stopAllGlbAnimations() {
    console.log("AVATAR - Stopping all GLB animations");
    
    // Store the current animation actions for reference
    const currentActions = {...currentAnimationActions};
    
    // Stop and clean up all action mixers except main mixer
    for (const mixer of animationMixers) {
      if (mixer !== mainAnimationMixer) {
        // Stop all actions on secondary mixers
        mixer.stopAllAction();
      }
    }
    
    // For the main mixer, stop actions individually with proper cleanup
    if (mainAnimationMixer) {
      // Keep only the main mixer
      animationMixers = [mainAnimationMixer];
      
      // Clear all current animations by stopping them properly
      Object.entries(currentActions).forEach(([path, action]) => {
        // Make sure action is enabled before stopping
        action.enabled = true;
        action.stop();
        
        // Remove from tracked actions
        delete currentAnimationActions[path];
      });
    } else {
      // If no main mixer, clear all mixers
      animationMixers = [];
      // Clear current actions
      currentAnimationActions = {};
    }
    
    // Reset animation state flags
    isPlayingGlbAnimation = false;
    isPlayingIdleGlbAnimation = false;
    
    console.log("AVATAR - All GLB animations stopped");
  }

  // Function to fade back to the default state
  function fadeToDefaultState() {
    console.log("AVATAR - Transitioning to default state with direct approach");
    
    // Immediately stop any gesture timers
    if (gestureTimer) {
      clearTimeout(gestureTimer);
      gestureTimer = null;
    }
    
    // Clear all active gesture flags immediately
    activeGesture = null;
    
    // Reset everything with our custom smooth transition
    resetAllAnimationState();
  }

  // Add this function to restore default pose and animation after speech ends
  function restoreDefaultState() {
    // Reset to default pose with hands down
    setDefaultPose();
    
    // Load the default idle animation
    loadGlbAnimation(ANIMATION_MAPPINGS.glbAnimations.idle.idle_default);
    
    console.log("AVATAR - Restored default pose and idle animation");
  }

  // Add the missing gesture functions
  function performHeadNod(intensity = 0.15) {
    return animateGenericBones('nod', intensity);
  }
  
  function performHeadShake(intensity = 0.15) {
    return animateGenericBones('shake', intensity);
  }
  
  function performForwardLean(intensity = 0.15) {
    return animateGenericBones('forward', intensity);
  }
  
  function performShoulderRaise(intensity = 0.15) {
    return animateGenericBones('shoulders', intensity);
  }
  
  function performExpressiveHandGesture(type = 'neutral', intensity = 0.15) {
    if (Object.keys(handBones).length === 0) return false;
    
    // Don't start a new animation if speech has already ended
    if (!isSpeaking) {
      console.log(`AVATAR - Not starting ${type} hand gesture because speech has ended`);
      return false;
    }
    
    const gestures = {
      'open': performHandWave,
      'defensive': () => animateGenericBones('lean_back', intensity),
      'neutral': () => {
        // Simple hand movement
        const handBonesList = Object.values(handBones);
        if (handBonesList.length === 0) return false;
        
        const randomBone = handBonesList[Math.floor(Math.random() * handBonesList.length)];
        const initialRot = initialRotations[randomBone.name] || { x: 0, y: 0, z: 0 };
        
        activeGesture = 'hand_gesture';
        
        const animateHand = () => {
          // If speech has ended or a different gesture is active, stop this animation immediately
          if (!isSpeaking || activeGesture !== 'hand_gesture') {
            randomBone.rotation.set(initialRot.x, initialRot.y, initialRot.z);
            if (activeGesture === 'hand_gesture') {
              activeGesture = null; // Only reset if this gesture is still the active one
            }
            return;
          }
          
          const time = Date.now() * 0.001;
          randomBone.rotation.x = initialRot.x + Math.sin(time) * intensity * 0.1;
          randomBone.rotation.y = initialRot.y + Math.sin(time * 1.3) * intensity * 0.1;
          
          requestAnimationFrame(animateHand);
        };
        
        animateHand();
        return true;
      }
    };
    
    if (gestures[type]) {
      return gestures[type](intensity);
    }
    
    return false;
  }
  
  function performExpression(expressionType) {
    if (!headMesh) return false;
    
    // Don't start a new animation if speech has already ended
    if (!isSpeaking) {
      console.log(`AVATAR - Not starting ${expressionType} expression because speech has ended`);
      return false;
    }
    
    // Track this expression with a name
    activeGesture = `expression_${expressionType}`;
    
    // Check if we have the expression morph target
    const expressionKey = EXPRESSIONS[expressionType];
    if (!expressionKey || headMesh.morphTargetDictionary[expressionKey] === undefined) {
      // Try to find a morph target that might work
      const possibleMorphs = Object.keys(headMesh.morphTargetDictionary).filter(key => 
        key.toLowerCase().includes(expressionType.toLowerCase())
      );
      
      if (possibleMorphs.length === 0) {
        console.log(`No morph target found for expression: ${expressionType}`);
        activeGesture = null;
        return false;
      }
      
      // Use the first matching morph
      const morphKey = possibleMorphs[0];
      const morphIndex = headMesh.morphTargetDictionary[morphKey];
      
      // Animate the expression with a bell curve
      // Use shorter duration to prevent expressions from lasting too long
      const duration = Math.min(ANIMATION_SETTINGS.expressionDuration, 1200);
      const startTime = Date.now();
      
      const animateExpression = () => {
        // If speech has ended or a different expression is active, stop immediately
        if (!isSpeaking || activeGesture !== `expression_${expressionType}`) {
          headMesh.morphTargetInfluences[morphIndex] = 0;
          if (activeGesture === `expression_${expressionType}`) {
            activeGesture = null; // Only reset if this expression is still active
          }
          return;
        }
        
        const elapsed = Date.now() - startTime;
        const progress = Math.min(1, elapsed / duration);
        
        // Bell curve for natural expression
        const value = Math.sin(progress * Math.PI) * ANIMATION_SETTINGS.expressionIntensity;
        headMesh.morphTargetInfluences[morphIndex] = value;
        
        if (progress < 1 && isSpeaking && activeGesture === `expression_${expressionType}`) {
          requestAnimationFrame(animateExpression);
        } else {
          headMesh.morphTargetInfluences[morphIndex] = 0;
          if (activeGesture === `expression_${expressionType}`) {
            activeGesture = null; // Only reset if this expression is still active
          }
        }
      };
      
      animateExpression();
      return true;
    } else {
      // We have the exact morph target
      const morphIndex = headMesh.morphTargetDictionary[expressionKey];
      
      // Animate the expression with a bell curve
      // Use shorter duration to prevent expressions from lasting too long
      const duration = Math.min(ANIMATION_SETTINGS.expressionDuration, 1200);
      const startTime = Date.now();
      
      const animateExpression = () => {
        // If speech has ended or a different expression is active, stop immediately
        if (!isSpeaking || activeGesture !== `expression_${expressionType}`) {
          headMesh.morphTargetInfluences[morphIndex] = 0;
          if (activeGesture === `expression_${expressionType}`) {
            activeGesture = null; // Only reset if this expression is still active
          }
          return;
        }
        
        const elapsed = Date.now() - startTime;
        const progress = Math.min(1, elapsed / duration);
        
        // Bell curve for natural expression
        const value = Math.sin(progress * Math.PI) * ANIMATION_SETTINGS.expressionIntensity;
        headMesh.morphTargetInfluences[morphIndex] = value;
        
        if (progress < 1 && isSpeaking && activeGesture === `expression_${expressionType}`) {
          requestAnimationFrame(animateExpression);
        } else {
          headMesh.morphTargetInfluences[morphIndex] = 0;
          if (activeGesture === `expression_${expressionType}`) {
            activeGesture = null; // Only reset if this expression is still active
          }
        }
      };
      
      animateExpression();
      return true;
    }
  }

  // Applies animation codes to the avatar
  function applyAnimations(animationCodes) {
    if (!animationCodes) return;
    
    console.log("Applying animations:", animationCodes);
    
    // Apply facial expression if specified
    if (animationCodes.facial_expression !== undefined) {
      const expressionCode = parseInt(animationCodes.facial_expression);
      const expressionType = ANIMATION_MAPPINGS.facialExpressions[expressionCode];
      
      if (expressionType) {
        performExpression(expressionType);
      }
    }
    
    // Apply head movement if specified
    if (animationCodes.head_movement !== undefined) {
      const headCode = parseInt(animationCodes.head_movement);
      const movementType = ANIMATION_MAPPINGS.headMovements[headCode];
      
      if (movementType === 'nod_small') {
        performHeadNod(0.1);
      } else if (movementType === 'shake') {
        performHeadShake(0.15);
      } else if (movementType === 'tilt') {
        animateGenericBones('tilt', 0.12);
      } else if (movementType === 'look_down') {
        animateGenericBones('head', 0.1);
      }
    }
    
    // Apply hand gesture if specified
    if (animationCodes.hand_gesture !== undefined) {
      const gestureCode = parseInt(animationCodes.hand_gesture);
      const gestureType = ANIMATION_MAPPINGS.handGestures[gestureCode];
      
      if (gestureType === 'wave') {
        performHandWave(0.2);
      } else if (gestureType === 'open_hand') {
        performExpressiveHandGesture('open', 0.15);
      } else if (gestureType === 'pointing') {
        performExpressiveHandGesture('neutral', 0.12);
      }
    }
    
    // Apply body posture if specified
    if (animationCodes.body_posture !== undefined) {
      const postureCode = parseInt(animationCodes.body_posture);
      const postureType = ANIMATION_MAPPINGS.bodyPostures[postureCode];
      
      if (postureType === 'forward_lean') {
        performForwardLean(0.15);
      } else if (postureType === 'lean_back') {
        animateGenericBones('lean_back', 0.12);
      } else if (postureType === 'shoulders_up') {
        performShoulderRaise(0.15);
      }
    }
  }

  // Add a new function to fully reset animation state to prevent looping animations
  function resetAllAnimationState() {
    console.log("AVATAR - Performing complete animation system reset");
    
    // First completely stop all current animations 
    // without any transitions to avoid weird movements
    for (const mixer of animationMixers) {
      mixer.stopAllAction();
    }
    
    // Clear animation tracking objects
    currentAnimationActions = {};
    activeGesture = null;
    
    // Reset animation state flags
    isPlayingGlbAnimation = false;
    isPlayingIdleGlbAnimation = false;
    stopEnhancedIdleAnimation();
    
    // Snapshot current bone positions
    const currentPositions = {};
    Object.values(allBones).forEach(bone => {
      if (bone && bone.name && bone.rotation) {
        currentPositions[bone.name] = {
          x: bone.rotation.x,
          y: bone.rotation.y,
          z: bone.rotation.z
        };
      }
    });
    
    // Reset all morph targets immediately
    if (headMesh && headMesh.morphTargetInfluences) {
      for (let i = 0; i < headMesh.morphTargetInfluences.length; i++) {
        headMesh.morphTargetInfluences[i] = 0;
      }
    }
    
    // First perform a short direct set to default 
    // (fixes the weird intermediate pose)
    setDefaultPose();
    
    // Then perform a very smooth transition from current positions
    // to the default pose using custom animation
    const duration = 800; // ms
    const startTime = Date.now();
    
    // Create a smooth animation function
    const smoothReset = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(1, elapsed / duration);
      
      // Smooth ease-in-out function
      const easeInOutQuint = t => t < 0.5 ? 16 * t * t * t * t * t : 1 - Math.pow(-2 * t + 2, 5) / 2;
      const easedProgress = easeInOutQuint(progress);
      
      // Get the target positions (which should be the default pose now)
      const targetPositions = {};
      Object.values(allBones).forEach(bone => {
        if (bone && bone.name) {
          targetPositions[bone.name] = {
            x: bone.rotation.x,
            y: bone.rotation.y,
            z: bone.rotation.z
          };
        }
      });
      
      // Now smoothly interpolate but with better curve for natural movement
      Object.values(allBones).forEach(bone => {
        if (bone && bone.name && currentPositions[bone.name] && targetPositions[bone.name]) {
          const current = currentPositions[bone.name];
          const target = targetPositions[bone.name];
          
          // Apply only a small amount of the full motion for more subtle movement
          bone.rotation.x = current.x + (target.x - current.x) * easedProgress;
          bone.rotation.y = current.y + (target.y - current.y) * easedProgress;
          bone.rotation.z = current.z + (target.z - current.z) * easedProgress;
        }
      });
      
      if (progress < 1) {
        requestAnimationFrame(smoothReset);
      } else {
        // When complete, load the default idle animation
        setTimeout(() => {
          if (!isSpeaking) {
            console.log("AVATAR - Loading default idle animation after reset");
            // Use loop repeat for the idle animation
            loadGlbAnimation(ANIMATION_MAPPINGS.glbAnimations.idle.idle_default, THREE.LoopRepeat, 0, 0.6);
          }
        }, 50);
      }
    };
    
    // Start the smooth transition
    requestAnimationFrame(smoothReset);
    
    console.log("AVATAR - Animation system fully reset");
  }

  // Add two new functions to handle the transition when animation ends
  function captureCurrentPose() {
    // Return a snapshot of current bone positions for smooth transitions
    const pose = {};
    if (avatar) {
      avatar.traverse((obj) => {
        if (obj.type === "Bone" && obj.name) {
          pose[obj.name] = {
            position: obj.position.clone(),
            rotation: obj.rotation.clone(),
            quaternion: obj.quaternion.clone()
          };
        }
      });
    }
    return pose;
  }

  // Function to animate directly between bone positions without using the animation system
  function directAnimateToPose(startPose, duration = 800) {
    if (!avatar) return;
    
    // Completely stop all animations immediately
    for (const mixer of animationMixers) {
      mixer.stopAllAction();
    }
    
    // Reset state flags and clear tracked animations
    currentAnimationActions = {};
    isPlayingGlbAnimation = false;
    isPlayingIdleGlbAnimation = false;
    activeGesture = null;
    
    // Rather than trying complex transitions, simply set the default pose directly
    setDefaultPose();
    
    // Reset any morph targets/blendshapes immediately
    if (headMesh && headMesh.morphTargetInfluences) {
      for (let i = 0; i < headMesh.morphTargetInfluences.length; i++) {
        headMesh.morphTargetInfluences[i] = 0;
      }
    }
    
    // Wait a short moment, then load the default idle animation
    setTimeout(() => {
      if (!isSpeaking) {
        console.log("Loading default idle animation");
        loadGlbAnimation(ANIMATION_MAPPINGS.glbAnimations.idle.idle_default);
      }
    }, 100);
  }
</script>

<div class={className}>
  <div class="w-full h-full relative">
    <div class="avatar-container w-full h-full" bind:this={avatarContainer}>
      {#if loading}
        <div class="loading-overlay">
          <Spinner size={48} />
          <p class="text-white mt-4">Loading Avatar...</p>
        </div>
      {/if}
    </div>
    
    <!-- Speaking indicator with integrated stop button -->
    {#if isSpeaking}
      <div class="speaking-indicator">
        <span class="dot animate-pulse"></span>
        <span class="text">Speaking...</span>
        <button 
          class="stop-speaking-button" 
          on:click={stopSpeaking}
          title="Stop Speaking"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-4 h-4">
            <path d="M5.47 5.47a.75.75 0 011.06 0L12 10.94l5.47-5.47a.75.75 0 111.06 1.06L13.06 12l5.47 5.47a.75.75 0 11-1.06 1.06L12 13.06l-5.47 5.47a.75.75 0 01-1.06-1.06L10.94 12 5.47 6.53a.75.75 0 010-1.06z" />
          </svg>
        </button>
      </div>
    {/if}
  </div>
</div>

<style>
  .avatar-container {
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .loading-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background-color: rgba(0, 0, 0, 0.5);
    z-index: 10;
  }
  
  .speaking-indicator {
    position: absolute;
    bottom: 16px;
    right: 16px;
    background-color: rgba(0, 0, 0, 0.6);
    color: white;
    padding: 4px 12px;
    border-radius: 16px;
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.75rem;
    animation: fadeIn 0.3s ease-in-out;
  }
  
  .stop-speaking-button {
    width: 20px;
    height: 20px;
    margin-left: 4px;
    background-color: rgba(239, 68, 68, 0.8);
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.2s ease-in-out;
    border: none;
    flex-shrink: 0;
  }
  
  .stop-speaking-button:hover {
    background-color: rgba(220, 38, 38, 0.9);
    transform: scale(1.1);
  }
  
  .stop-speaking-button:active {
    transform: scale(0.9);
  }
  
  .dot {
    width: 8px;
    height: 8px;
    background-color: #4a63ee;
    border-radius: 50%;
  }
  
  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }
</style> 