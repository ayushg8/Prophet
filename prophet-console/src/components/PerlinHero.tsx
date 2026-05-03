import { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { createNoise3D } from 'simplex-noise';

type Props = {
  className?: string;
  /** Mesh grid segments. Default 96 (landing). Use 64 on the console for lower GPU cost. */
  segments?: number;
};

export function PerlinHero({ className, segments = 96 }: Props) {
  const mountRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;

    const width = mount.clientWidth;
    const height = mount.clientHeight;

    const scene = new THREE.Scene();
    scene.fog = new THREE.Fog(0x0a0d12, 14, 42);

    const camera = new THREE.PerspectiveCamera(55, width / height, 0.1, 200);
    camera.position.set(0, 9, 18);
    camera.lookAt(0, -1, 0);

    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
      powerPreference: 'high-performance',
    });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(width, height);
    renderer.setClearColor(0x000000, 0);
    mount.appendChild(renderer.domElement);

    const SIZE = 48;
    const geometry = new THREE.PlaneGeometry(SIZE, SIZE, segments, segments);
    geometry.rotateX(-Math.PI / 2);

    const material = new THREE.LineBasicMaterial({
      color: 0xf59e0b,
      transparent: true,
      opacity: 0.55,
    });
    const wire = new THREE.WireframeGeometry(geometry);
    const wireMesh = new THREE.LineSegments(wire, material);
    scene.add(wireMesh);

    const ghostMaterial = new THREE.MeshBasicMaterial({
      color: 0x161b22,
      transparent: true,
      opacity: 0.7,
      side: THREE.DoubleSide,
    });
    const ghostMesh = new THREE.Mesh(geometry, ghostMaterial);
    ghostMesh.position.y = -0.05;
    scene.add(ghostMesh);

    const noise3D = createNoise3D();

    const positionAttr = geometry.attributes.position as THREE.BufferAttribute;
    const initialPositions = positionAttr.array.slice() as Float32Array;

    let frameId = 0;
    const start = performance.now();

    const onResize = () => {
      const w = mount.clientWidth;
      const h = mount.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener('resize', onResize);

    const animate = () => {
      const t = (performance.now() - start) / 1000;

      const arr = positionAttr.array as Float32Array;
      for (let i = 0; i < arr.length; i += 3) {
        const x = initialPositions[i];
        const z = initialPositions[i + 2];
        const n =
          noise3D(x * 0.08, z * 0.08, t * 0.18) * 1.6 +
          noise3D(x * 0.22, z * 0.22, t * 0.32) * 0.45;
        arr[i + 1] = n;
      }
      positionAttr.needsUpdate = true;

      const updatedWire = new THREE.WireframeGeometry(geometry);
      wireMesh.geometry.dispose();
      wireMesh.geometry = updatedWire;

      ghostMesh.rotation.y = Math.sin(t * 0.04) * 0.04;
      wireMesh.rotation.y = ghostMesh.rotation.y;

      renderer.render(scene, camera);
      frameId = requestAnimationFrame(animate);
    };
    animate();

    return () => {
      cancelAnimationFrame(frameId);
      window.removeEventListener('resize', onResize);
      renderer.dispose();
      geometry.dispose();
      material.dispose();
      ghostMaterial.dispose();
      wire.dispose();
      if (renderer.domElement.parentNode === mount) {
        mount.removeChild(renderer.domElement);
      }
    };
  }, [segments]);

  return <div ref={mountRef} className={className} />;
}
