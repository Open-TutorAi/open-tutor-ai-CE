<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import * as THREE from 'three';
  
  // Props
  export let scene: THREE.Scene | null = null;
  export let message: string = "BOARD TEXT EXAMPLE\n\nThis text should be clearly visible on the chalkboard.";
  export let position = { x: 0.2, y: 1.0, z: -3.3 }; // Shifted right by adjusting x from 0 to 0.2
  export let width = 2200;  // Width in pixels
  export let height = 1000;  // Height in pixels
  export let debug = false; // Disable debug mode by default
  export let viewType: 'front-view' | 'side-view' = 'front-view'; // Which view type
  export let camera: THREE.PerspectiveCamera | null = null;  // Add camera prop

  let boardMesh: THREE.Mesh | null = null;
  let debugHelper: THREE.Group | null = null;
  let animationFrame: number | null = null;
  let currentText = '';
  let targetText = '';
  let lastUpdateTime = 0;
  const CHAR_DELAY = 65; // Increased from 30 to 50 milliseconds for slower animation

  // Pagination state
  let allPages: string[] = [];
  let currentPageIndex = 0;
  let navigationMeshes: THREE.Mesh[] = [];
  const LINES_PER_PAGE = 10; // Changed to 10 lines per page

  // Arrow geometry and materials
  const arrowGeometry = new THREE.PlaneGeometry(0.3, 0.3);
  const arrowMaterialLeft = new THREE.MeshBasicMaterial({
    map: createArrowTexture('←'),
    transparent: true,
    opacity: 0.9,
    side: THREE.DoubleSide
  });
  const arrowMaterialRight = new THREE.MeshBasicMaterial({
    map: createArrowTexture('→'),
    transparent: true,
    opacity: 0.9,
    side: THREE.DoubleSide
  });

  // Create arrow texture
  function createArrowTexture(symbol: string): THREE.Texture {
    const canvas = document.createElement('canvas');
    canvas.width = 64;
    canvas.height = 64;
    const context = canvas.getContext('2d');
    if (context) {
      context.fillStyle = 'white';
      context.font = 'bold 48px Arial';
      context.textAlign = 'center';
      context.textBaseline = 'middle';
      context.fillText(symbol, 32, 32);
    }
    const texture = new THREE.CanvasTexture(canvas);
    texture.needsUpdate = true;
    return texture;
  }

  // Define board dimensions precisely for each view type
  const boardDimensions = {
    'front-view': {
      width: 3.6,      // Slightly reduced width
      height: 1.8,     // Slightly reduced height
      zOffset: 0.01    // Tiny offset to prevent z-fighting
    },
    'side-view': {
      width: 3.2,      // Slightly reduced width
      height: 1.6,     // Slightly reduced height
      zOffset: 0.01
    }
  };

  // Function to animate text
  function animateText(timestamp: number) {
    if (!lastUpdateTime) lastUpdateTime = timestamp;
    
    const deltaTime = timestamp - lastUpdateTime;
    
    if (deltaTime >= CHAR_DELAY && currentText !== targetText) {
      // Add next character
      currentText = targetText.slice(0, currentText.length + 1);
      lastUpdateTime = timestamp;
      
      // Update the board with current text
      if (scene && boardMesh) {
        scene.remove(boardMesh);
        createBoardText(currentText);
      }
    }
    
    // Continue animation if not complete
    if (currentText !== targetText) {
      animationFrame = requestAnimationFrame(animateText);
    }
  }

  // Add a function to parse potential JSON content
  function parseMessageContent(content: string): string {
    console.log("Original message content:", content);
    
    // First, remove the text \`\`\`json
    // (this handles cases where it appears as literal text instead of markdown)
    if (content.includes('\`\`\`json')) {
      console.log("Found literal markdown markers");
      content = content.replace(/\`\`\`json/g, '');
      content = content.replace(/\`\`\`/g, '');
      console.log("Cleaned content:", content);
    }
    
    // Direct regex extraction of "response" field
    // This is a fallback approach that directly looks for the response pattern we see in screenshots
    const directResponseMatch = content.match(/"response"\s*:\s*"([^"]+)"/);
    if (directResponseMatch && directResponseMatch[1]) {
      console.log("Found response via direct pattern matching:", directResponseMatch[1]);
      return directResponseMatch[1];
    }
    
    // Check if the content starts with ```json (markdown code block)
    if (content.trim().startsWith('```json') || content.includes('```json')) {
      console.log("Found markdown code block with JSON");
      // Try different patterns to extract the JSON content
      let jsonText = '';
      
      // Pattern 1: Standard markdown code block
      const codeBlockMatch = content.match(/```json\s*([\s\S]*?)```/);
      if (codeBlockMatch && codeBlockMatch[1]) {
        jsonText = codeBlockMatch[1].trim();
      } 
      // Pattern 2: If the closing ``` is missing
      else if (content.includes('```json')) {
        jsonText = content.split('```json')[1].trim();
      }
      
      if (jsonText) {
        console.log("Extracted JSON from code block:", jsonText);
        try {
          // Try to parse it as JSON
          const jsonContent = JSON.parse(jsonText);
          console.log("Successfully parsed JSON from code block");
          
          // If it has a response field, use that
          if (jsonContent.response) {
            console.log("Found response field:", jsonContent.response);
            return jsonContent.response;
          }
        } catch (e) {
          console.error("Failed to parse JSON code block:", e);
        }
      }
    }
    
    // Check if the content seems to be JSON (starts with { and ends with })
    if (content.trim().startsWith('{') && content.trim().endsWith('}')) {
      console.log("Content appears to be raw JSON");
      try {
        // Try to parse it as JSON
        const jsonContent = JSON.parse(content);
        console.log("Successfully parsed raw JSON");
        
        // If it has a response field, use that
        if (jsonContent.response) {
          console.log("Found response field in raw JSON:", jsonContent.response);
          return jsonContent.response;
        }
      } catch (e) {
        // If parsing fails, just use the original content
        console.error("Failed to parse JSON content:", e);
      }
    }
    
    console.log("No JSON structure detected, returning original content");
    // Return original content if not JSON or no response field
    return content;
  }

  // Modified createBoardText to accept current text
  function createBoardText(displayText?: string) {
    if (!scene) return;
    
    console.log("Creating board text at position:", position);
    
    // Get dimensions for current view type
    const dims = boardDimensions[viewType];
    
    // Create a canvas texture for the text
    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    
    const context = canvas.getContext('2d');
    
    if (!context) {
      console.error("Could not get canvas context");
      return;
    }
    
    // Make the canvas fully transparent
    context.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw text
    context.fillStyle = 'white';
    context.font = 'bold 65px Arial, sans-serif';
    context.textAlign = 'left';
    context.textBaseline = 'top';
    
    // Calculate the maximum width for text wrapping
    const maxTextWidth = canvas.width - 300; // Increased margin for better readability
    
    // Use provided display text or get it from message
    const textToDisplay = displayText || parseMessageContent(message);
    
    // Split the message into paragraphs
    const paragraphs = textToDisplay.split('\n');
    let y = 50;
    const lineHeight = 80;
    let lineCount = 0;
    
    for (const paragraph of paragraphs) {
      if (paragraph === '') {
        y += lineHeight;
        lineCount++;
        if (lineCount >= LINES_PER_PAGE) break;
        continue;
      }
      
      const wrappedLines = wrapText(context, paragraph, maxTextWidth);
      
      for (const line of wrappedLines) {
        if (lineCount >= LINES_PER_PAGE) break;
        context.fillText(line, 150, y);
        y += lineHeight;
        lineCount++;
      }
      
      if (lineCount >= LINES_PER_PAGE) break;
    }
    
    // Create texture and material
    const texture = new THREE.CanvasTexture(canvas);
    texture.minFilter = THREE.LinearFilter;
    texture.magFilter = THREE.LinearFilter;
    
    const material = new THREE.MeshBasicMaterial({
      map: texture,
      transparent: true,
      opacity: 1.0,
      side: THREE.DoubleSide,
      alphaTest: 0.01
    });
    
    const geometry = new THREE.PlaneGeometry(dims.width, dims.height);
    boardMesh = new THREE.Mesh(geometry, material);
    boardMesh.position.set(position.x, position.y, position.z + 0.01);
    
    if (viewType === 'front-view') {
      boardMesh.rotation.set(0, 0, 0);
    } else {
      boardMesh.rotation.set(0, -Math.PI/2, 0);
    }
    
    scene.add(boardMesh);
    createNavigationArrows();
  }

  function createNavigationArrows() {
    // Remove existing navigation meshes
    navigationMeshes.forEach(mesh => {
      if (scene) scene.remove(mesh);
    });
    navigationMeshes = [];

    if (!scene || allPages.length <= 1) return;

    console.log('Creating navigation arrows. Current page:', currentPageIndex, 'Total pages:', allPages.length);

    // Create left arrow if not on first page
    if (currentPageIndex > 0) {
      const leftArrow = new THREE.Mesh(arrowGeometry, arrowMaterialLeft);
      // Position left arrow slightly to the left of center
      leftArrow.position.set(position.x + 1.5, position.y, position.z + 0.02);
      leftArrow.userData.isLeftArrow = true;
      navigationMeshes.push(leftArrow);
      scene.add(leftArrow);
      console.log('Left arrow added');
    }

    // Create right arrow if not on last page
    if (currentPageIndex < allPages.length - 1) {
      const rightArrow = new THREE.Mesh(arrowGeometry, arrowMaterialRight);
      // Position right arrow slightly to the right of center
      rightArrow.position.set(position.x + 1.8, position.y, position.z + 0.02);
      rightArrow.userData.isRightArrow = true;
      navigationMeshes.push(rightArrow);
      scene.add(rightArrow);
      console.log('Right arrow added');
    }
  }

  function splitIntoPages(text: string): string[] {
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    if (!context) return [text];
    
    context.font = 'bold 65px Arial, sans-serif';
    const maxTextWidth = width - 300;
    
    const words = text.split(' ');
    const pages: string[] = [];
    let currentPage: string[] = [];
    let currentLine: string[] = [];
    let lineCount = 0;
    
    for (let i = 0; i < words.length; i++) {
      const word = words[i];
      const testLine = [...currentLine, word].join(' ');
      const metrics = context.measureText(testLine);
      
      if (metrics.width <= maxTextWidth) {
        currentLine.push(word);
      } else {
        if (lineCount >= LINES_PER_PAGE) {
          pages.push(currentPage.join('\n'));
          currentPage = [];
          lineCount = 0;
        }
        
        if (currentLine.length > 0) {
          currentPage.push(currentLine.join(' '));
          lineCount++;
        }
        currentLine = [word];
      }
      
      // Handle line breaks in the text
      if (word.includes('\n')) {
        if (currentLine.length > 0) {
          if (lineCount >= LINES_PER_PAGE) {
            pages.push(currentPage.join('\n'));
            currentPage = [];
            lineCount = 0;
          }
          currentPage.push(currentLine.join(' '));
          lineCount++;
        }
        currentLine = [];
      }
    }
    
    // Add remaining line if exists
    if (currentLine.length > 0) {
      if (lineCount >= LINES_PER_PAGE) {
        pages.push(currentPage.join('\n'));
        currentPage = [];
      }
      currentPage.push(currentLine.join(' '));
    }
    
    // Add remaining page if exists
    if (currentPage.length > 0) {
      pages.push(currentPage.join('\n'));
    }
    
    return pages;
  }

  function navigateToPage(pageIndex: number) {
    console.log('Attempting to navigate to page:', pageIndex);
    console.log('Total pages:', allPages.length);
    
    if (pageIndex >= 0 && pageIndex < allPages.length) {
      // Cancel any ongoing animation first
      if (animationFrame !== null) {
        cancelAnimationFrame(animationFrame);
        animationFrame = null;
      }

      currentPageIndex = pageIndex;
      
      // Clear existing board
      if (scene && boardMesh) {
        scene.remove(boardMesh);
        boardMesh = null;
      }
      
      // Start fresh animation for the new page
      currentText = '';
      targetText = allPages[currentPageIndex];
      lastUpdateTime = 0;
      
      // Create initial empty board and start animation
      createBoardText(currentText);
      animationFrame = requestAnimationFrame(animateText);
      
      // Update arrows after changing page
      createNavigationArrows();
    }
  }

  // Modified startTextAnimation to ensure pagination works
  function startTextAnimation(newMessage: string) {
    if (animationFrame !== null) {
      cancelAnimationFrame(animationFrame);
    }

    const processedText = parseMessageContent(newMessage);
    allPages = splitIntoPages(processedText);
    console.log('Pages created:', allPages.length, 'Content:', allPages);
    
    currentPageIndex = 0;
    currentText = '';
    targetText = allPages[currentPageIndex];
    lastUpdateTime = 0;
    
    if (scene) {
      // Clear existing board and arrows
      if (boardMesh) scene.remove(boardMesh);
      navigationMeshes.forEach(mesh => scene.remove(mesh));
      
      // Create new board and arrows
      createBoardText(currentText);
      createNavigationArrows();
    }
    
    animationFrame = requestAnimationFrame(animateText);
  }

  // Handle click events for navigation
  function handleClick(event: MouseEvent) {
    if (!scene || !camera) return;

    // Calculate mouse position in normalized device coordinates (-1 to +1)
    const rect = (event.target as HTMLElement).getBoundingClientRect();
    const x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    const y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2(x, y);

    // Update the picking ray with the camera and mouse position
    raycaster.setFromCamera(mouse, camera);

    // Calculate objects intersecting the picking ray
    const intersects = raycaster.intersectObjects(navigationMeshes, true);
    
    if (intersects.length > 0) {
      const mesh = intersects[0].object;
      console.log('Arrow clicked:', mesh.userData);
      
      // Allow navigation regardless of animation state
      if (mesh.userData.isLeftArrow && currentPageIndex > 0) {
        console.log('Navigating to previous page:', currentPageIndex - 1);
        navigateToPage(currentPageIndex - 1);
      } else if (mesh.userData.isRightArrow && currentPageIndex < allPages.length - 1) {
        console.log('Navigating to next page:', currentPageIndex + 1);
        navigateToPage(currentPageIndex + 1);
      }
    }
  }

  // Add window resize handler to update arrow positions
  function handleResize() {
    if (scene) {
      createNavigationArrows();
    }
  }

  onMount(() => {
    if (scene) {
      startTextAnimation(message);
      if (debug) {
        createDebugHelpers();
      }
      
      // Add event listeners
      window.addEventListener('click', handleClick);
      window.addEventListener('resize', handleResize);
    }
    
    return () => {
      if (animationFrame !== null) {
        cancelAnimationFrame(animationFrame);
      }
      if (boardMesh && scene) {
        scene.remove(boardMesh);
      }
      if (debugHelper && scene) {
        scene.remove(debugHelper);
      }
      navigationMeshes.forEach(mesh => {
        if (scene) scene.remove(mesh);
      });
      
      // Remove event listeners
      window.removeEventListener('click', handleClick);
      window.removeEventListener('resize', handleResize);
    };
  });

  // Function to wrap text based on maximum width
  function wrapText(context: CanvasRenderingContext2D, text: string, maxWidth: number): string[] {
    const words = text.split(' ');
    const lines = [];
    let currentLine = words[0];

    for (let i = 1; i < words.length; i++) {
      const word = words[i];
      const width = context.measureText(currentLine + ' ' + word).width;
      
      if (width < maxWidth) {
        currentLine += ' ' + word;
      } else {
        lines.push(currentLine);
        currentLine = word;
      }
    }
    
    lines.push(currentLine);
    return lines;
  }
  
  function createDebugHelpers() {
    if (!scene) return;
    
    debugHelper = new THREE.Group();
    
    // Create a visual marker for the board position
    const markerGeometry = new THREE.SphereGeometry(0.02, 16, 16);
    const markerMaterial = new THREE.MeshBasicMaterial({ color: 0xff0000 });
    const marker = new THREE.Mesh(markerGeometry, markerMaterial);
    marker.position.set(position.x, position.y, position.z);
    debugHelper.add(marker);
    
    // Add axis helper for debugging orientation
    const axisHelper = new THREE.AxesHelper(0.3);
    axisHelper.position.set(position.x, position.y, position.z);
    debugHelper.add(axisHelper);
    
    scene.add(debugHelper);
    console.log("Debug helpers added");
  }

  // Watch for message changes
  $: if (message && scene) {
    console.log("Message changed, updating board text with animation");
    startTextAnimation(message);
  }
  
  // Watch for view type changes
  $: if (viewType && scene) {
    if (boardMesh) {
      scene.remove(boardMesh);
      boardMesh = null;
    }
    if (debugHelper) {
      scene.remove(debugHelper);
      debugHelper = null;
    }
    navigationMeshes.forEach(mesh => {
      if (scene) scene.remove(mesh);
    });
    
    createBoardText(currentText);
    if (debug) {
      createDebugHelpers();
    }
  }
  
  // Watch for position changes
  $: if (position && scene) {
    if (boardMesh) {
      boardMesh.position.set(position.x, position.y, position.z + 0.01);
      
      // Update rotation
      if (viewType === 'front-view') {
        boardMesh.rotation.set(0, 0, 0);
      } else {
        boardMesh.rotation.set(0, -Math.PI/2, 0);
      }
    }
    
    // Update navigation arrows position
    createNavigationArrows();
    
    if (debugHelper) {
      scene.remove(debugHelper);
      debugHelper = null;
      createDebugHelpers();
    }
  }
</script> 