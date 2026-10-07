/**
 * ELECTROCART Hero WebGL Scene Module (WP7).
 * Tier 1 only, dynamically loaded on homepage hero plate.
 *
 * Rules:
 * - Single plane carrying product photo floats over a soft plinth.
 * - Multiply-blended in custom shader so white background matches world background.
 * - Gentle idle drift, pointer parallax, initial specular light sweep on entry.
 * - Cap devicePixelRatio at 1.75 (1.5 on tablet). Antialias off, powerPreference "default".
 * - Render on demand: runs only when hero is visible in viewport and document is visible.
 * - Disposes geometry, material, texture, renderer on removal or context lost.
 * - Checks GLTFLoader for hero-model-1.glb; when absent, uses photo plane scene.
 * - Fallback HTML plate stays underneath in the DOM.
 */

import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";

let activeSceneContext = null;

/**
 * Initializes the WebGL Hero Scene inside the hero container.
 *
 * @param {HTMLElement} mountContainer - The container element to mount the canvas
 * @param {string} imageUrl - Product photo URL to texture
 * @param {string} worldBgHex - World background color hex string (e.g. #F5F2EB)
 * @returns {Object|null}
 */
export function initHeroWebGL(mountContainer, imageUrl, worldBgHex = "#F5F2EB") {
  teardownHeroWebGL();

  if (!mountContainer || !imageUrl) return null;

  const width = mountContainer.clientWidth || 360;
  const height = mountContainer.clientHeight || 360;

  // Scene & Camera
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
  camera.position.z = 4.2;

  // WebGL Renderer with strict budget constraints
  let renderer = null;
  try {
    renderer = new THREE.WebGLRenderer({
      alpha: true,
      antialias: false,
      powerPreference: "default",
    });
  } catch (err) {
    console.warn("Could not create Three.js WebGLRenderer:", err);
    return null;
  }

  const dpr = Math.min(window.innerWidth < 1024 ? 1.5 : 1.75, window.devicePixelRatio || 1);
  renderer.setPixelRatio(dpr);
  renderer.setSize(width, height);
  renderer.domElement.setAttribute("aria-hidden", "true");
  renderer.domElement.style.position = "absolute";
  renderer.domElement.style.top = "0";
  renderer.domElement.style.left = "0";
  renderer.domElement.style.width = "100%";
  renderer.domElement.style.height = "100%";
  renderer.domElement.style.pointerEvents = "none";
  renderer.domElement.style.zIndex = "2";

  mountContainer.style.position = "relative";
  mountContainer.appendChild(renderer.domElement);

  // Background color parsing for multiply shader
  const worldColor = new THREE.Color(worldBgHex);

  // Create Texture with anonymous CORS
  const textureLoader = new THREE.TextureLoader();
  textureLoader.setCrossOrigin("anonymous");

  let photoMesh = null;
  let plinthMesh = null;
  let sweepStartTime = null;
  let isRunning = true;
  let rafId = null;

  // 1. Plinth Shadow Disc
  const plinthGeo = new THREE.CircleGeometry(1.2, 32);
  const plinthMat = new THREE.MeshBasicMaterial({
    color: 0x000000,
    transparent: true,
    opacity: 0.08,
  });
  plinthMesh = new THREE.Mesh(plinthGeo, plinthMat);
  plinthMesh.rotation.x = -Math.PI / 2;
  plinthMesh.position.y = -1.2;
  scene.add(plinthMesh);

  // 2. Custom Multiply Shader Material for Product Photo Plane
  const vertexShader = `
    varying vec2 vUv;
    void main() {
      vUv = uv;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    }
  `;

  const fragmentShader = `
    uniform sampler2D uTexture;
    uniform vec3 uWorldBg;
    uniform float uSweepProgress;
    varying vec2 vUv;

    void main() {
      vec4 texColor = texture2D(uTexture, vUv);
      // Multiply blend: white pixels blend into uWorldBg
      vec3 multiplied = texColor.rgb * uWorldBg;

      // Specular light sweep diagonal band
      float diag = vUv.x * 0.7 + vUv.y * 0.3;
      float band = smoothstep(uSweepProgress - 0.2, uSweepProgress, diag) - 
                   smoothstep(uSweepProgress, uSweepProgress + 0.2, diag);
      vec3 colorWithSweep = multiplied + vec3(band * 0.18);

      gl_FragColor = vec4(colorWithSweep, texColor.a);
    }
  `;

  const uniforms = {
    uTexture: { value: null },
    uWorldBg: { value: worldColor },
    uSweepProgress: { value: -0.5 },
  };

  const photoMat = new THREE.ShaderMaterial({
    vertexShader,
    fragmentShader,
    uniforms,
    transparent: true,
  });

  const photoGeo = new THREE.PlaneGeometry(2.2, 2.2);
  photoMesh = new THREE.Mesh(photoGeo, photoMat);
  scene.add(photoMesh);

  // Load product texture
  textureLoader.load(
    imageUrl,
    (texture) => {
      texture.minFilter = THREE.LinearFilter;
      texture.generateMipmaps = false;
      uniforms.uTexture.value = texture;
      sweepStartTime = performance.now();
    },
    undefined,
    () => {
      // Fallback: hide canvas if texture loading fails (CORS or network)
      if (renderer && renderer.domElement) {
        renderer.domElement.style.display = "none";
      }
    }
  );

  // 3. Optional GLTF 3D Model Loader path (ASSETS.md: hero-model-1.glb)
  const modelUrl =
    mountContainer.dataset.heroModel ||
    (mountContainer.parentElement && mountContainer.parentElement.dataset.heroModel);
  if (modelUrl) {
    const gltfLoader = new GLTFLoader();
    gltfLoader.load(
      modelUrl,
      (gltf) => {
        if (photoMesh) {
          scene.remove(photoMesh);
        }
        const model = gltf.scene;
        model.scale.set(1.5, 1.5, 1.5);
        model.position.y = -0.2;
        scene.add(model);
        photoMesh = model;
      },
      undefined,
      (err) => {
        console.warn("Optional GLTF model not loaded:", err);
      }
    );
  }

  // Pointer Parallax variables
  let targetRotX = 0;
  let targetRotY = 0;

  function onPointerMove(e) {
    const rect = mountContainer.getBoundingClientRect();
    const nx = (e.clientX - rect.left) / rect.width - 0.5;
    const ny = (e.clientY - rect.top) / rect.height - 0.5;
    targetRotY = nx * 0.18;
    targetRotX = -ny * 0.18;
  }

  function onPointerLeave() {
    targetRotX = 0;
    targetRotY = 0;
  }

  window.addEventListener("pointermove", onPointerMove, { passive: true });
  mountContainer.addEventListener("pointerleave", onPointerLeave, { passive: true });

  // WebGL Context Lost recovery
  const canvas = renderer.domElement;
  function onContextLost(e) {
    e.preventDefault();
    teardownHeroWebGL();
  }
  canvas.addEventListener("webglcontextlost", onContextLost);

  // Animation Loop
  function tick(timestamp) {
    if (!isRunning) return;

    // Specular sweep across first 2.5 seconds
    if (sweepStartTime !== null) {
      const elapsed = (timestamp - sweepStartTime) / 1000;
      if (elapsed < 2.5) {
        uniforms.uSweepProgress.value = -0.4 + elapsed * 0.7;
      } else {
        uniforms.uSweepProgress.value = 2.0; // out of view
      }
    }

    // Gentle idle drift & parallax damping
    if (photoMesh) {
      photoMesh.position.y = Math.sin(timestamp * 0.0012) * 0.04;
      photoMesh.rotation.x += (targetRotX - photoMesh.rotation.x) * 0.06;
      photoMesh.rotation.y += (targetRotY - photoMesh.rotation.y) * 0.06;
    }

    if (plinthMesh) {
      plinthMesh.scale.x = 1.0 + Math.sin(timestamp * 0.0012) * 0.03;
      plinthMesh.scale.y = 1.0 + Math.sin(timestamp * 0.0012) * 0.03;
    }

    renderer.render(scene, camera);
    rafId = window.requestAnimationFrame(tick);
  }

  rafId = window.requestAnimationFrame(tick);

  // Resize handler
  function onResize() {
    if (!mountContainer || !renderer) return;
    const newW = mountContainer.clientWidth;
    const newH = mountContainer.clientHeight;
    camera.aspect = newW / newH;
    camera.updateProjectionMatrix();
    renderer.setSize(newW, newH);
  }
  window.addEventListener("resize", onResize);

  activeSceneContext = {
    pause: () => {
      isRunning = false;
      if (rafId) window.cancelAnimationFrame(rafId);
    },
    resume: () => {
      if (!isRunning) {
        isRunning = true;
        rafId = window.requestAnimationFrame(tick);
      }
    },
    destroy: () => {
      isRunning = false;
      if (rafId) window.cancelAnimationFrame(rafId);
      window.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("resize", onResize);
      canvas.removeEventListener("webglcontextlost", onContextLost);

      // Dispose Three.js objects
      try {
        if (photoGeo) photoGeo.dispose();
        if (photoMat) photoMat.dispose();
        if (plinthGeo) plinthGeo.dispose();
        if (plinthMat) plinthMat.dispose();
        if (uniforms.uTexture.value) uniforms.uTexture.value.dispose();
        renderer.dispose();
        if (canvas.parentNode) canvas.parentNode.removeChild(canvas);
      } catch (_) {}
      activeSceneContext = null;
    },
  };

  return activeSceneContext;
}

/**
 * Tears down and disposes the active WebGL scene.
 */
export function teardownHeroWebGL() {
  if (activeSceneContext) {
    activeSceneContext.destroy();
    activeSceneContext = null;
  }
}

/**
 * Pauses rendering loop (e.g. when hero leaves view or tab hidden).
 */
export function pauseHeroWebGL() {
  if (activeSceneContext) {
    activeSceneContext.pause();
  }
}

/**
 * Resumes rendering loop.
 */
export function resumeHeroWebGL() {
  if (activeSceneContext) {
    activeSceneContext.resume();
  }
}
