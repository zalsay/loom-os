import * as THREE from 'three';

const VIEWS = { front: 0, quarter: Math.PI / 6, side: Math.PI / 2, back: Math.PI };
export function viewPosition(name, distance = 8) {
  if (!Object.hasOwn(VIEWS, name)) throw new Error(`Unknown view: ${name}`);
  return new THREE.Vector3(Math.sin(VIEWS[name]) * distance, distance * 0.045, Math.cos(VIEWS[name]) * distance);
}
export function frameModel(bounds, aspect, fov) {
  if (!Number.isFinite(aspect) || aspect <= 0) throw new Error('Invalid aspect ratio');
  const size = bounds.getSize(new THREE.Vector3());
  const vertical = THREE.MathUtils.degToRad(fov) / 2;
  const horizontal = Math.atan(Math.tan(vertical) * aspect);
  const distance = Math.max(size.y / (2 * Math.tan(vertical)), size.x / (2 * Math.tan(horizontal))) * 1.16 + size.z * 0.5;
  return { target: bounds.getCenter(new THREE.Vector3()), distance };
}

export function createStudio(renderer, pixelRatio = 1) {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#eae7dd');
  renderer.setPixelRatio(Math.min(pixelRatio || 1, 2));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFShadowMap;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;
  scene.add(new THREE.HemisphereLight('#fff6e4', '#b6b3a9', 1.8));
  const light = (name, color, intensity, position, shadow = false) => {
    const lamp = new THREE.DirectionalLight(color, intensity); lamp.name = name;
    lamp.position.set(...position); lamp.castShadow = shadow;
    if (shadow) {
      lamp.shadow.mapSize.set(2048, 2048);
      Object.assign(lamp.shadow.camera, { left: -4, right: 4, top: 6, bottom: -2, near: 0.1, far: 20 });
      lamp.shadow.normalBias = 0.025; lamp.shadow.bias = -0.0002; lamp.shadow.radius = 24;
    }
    scene.add(lamp); return lamp;
  };
  light('large warm key', '#fff5dc', 3.5, [-2, 8, 3], true);
  light('cool fill', '#d6e7e5', 1.15, [4, 4, 3]);
  light('soft rim', '#fff6df', 2.0, [1, 5, -4]);
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(200,200),new THREE.ShadowMaterial({color:'#747563',opacity:0.16}));
  ground.name='studio floor'; ground.rotation.x=-Math.PI/2;ground.position.y=-0.025;ground.receiveShadow=true;scene.add(ground);
  return scene;
}
