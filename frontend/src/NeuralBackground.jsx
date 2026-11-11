import { useEffect, useRef, useState } from 'react'
import * as THREE from 'three'

const reduceMotionQuery = '(prefers-reduced-motion: reduce)'

function makeSpherePoints(count, radius) {
  const positions = []
  const colors = []
  const points = []
  const goldenAngle = Math.PI * (3 - Math.sqrt(5))

  for (let index = 0; index < count; index += 1) {
    const y = 1 - (index / (count - 1)) * 2
    const ringRadius = Math.sqrt(1 - y * y)
    const angle = goldenAngle * index
    const point = new THREE.Vector3(
      Math.cos(angle) * ringRadius * radius,
      y * radius,
      Math.sin(angle) * ringRadius * radius
    )
    points.push(point)
    positions.push(point.x, point.y, point.z)

    const color = new THREE.Color(index % 5 === 0 ? 0x9d8aff : 0x63e5f2)
    colors.push(color.r, color.g, color.b)
  }

  return { positions, colors, points }
}

function createNetwork(count, radius) {
  const network = new THREE.Group()
  const { positions, colors, points } = makeSpherePoints(count, radius)
  const nodeGeometry = new THREE.BufferGeometry()
  nodeGeometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3))
  nodeGeometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3))
  network.add(new THREE.Points(nodeGeometry, new THREE.PointsMaterial({
    size: 0.075,
    vertexColors: true,
    transparent: true,
    opacity: 0.92,
    sizeAttenuation: true,
    blending: THREE.AdditiveBlending,
    depthWrite: false
  })))

  const edgePositions = []
  const edges = []
  const edgeKeys = new Set()
  points.forEach((point, index) => {
    const nearest = points
      .map((other, otherIndex) => ({ other, otherIndex, distance: point.distanceToSquared(other) }))
      .filter(({ otherIndex }) => otherIndex !== index)
      .sort((a, b) => a.distance - b.distance)
      .slice(0, 3)

    nearest.forEach(({ other, otherIndex }) => {
      const start = Math.min(index, otherIndex)
      const end = Math.max(index, otherIndex)
      const key = `${start}-${end}`
      if (edgeKeys.has(key)) return
      edgeKeys.add(key)
      edgePositions.push(...point.toArray(), ...other.toArray())
      edges.push([points[start], points[end]])
    })
  })

  const edgeGeometry = new THREE.BufferGeometry()
  edgeGeometry.setAttribute('position', new THREE.Float32BufferAttribute(edgePositions, 3))
  network.add(new THREE.LineSegments(edgeGeometry, new THREE.LineBasicMaterial({
    color: 0x5bcfe4,
    transparent: true,
    opacity: 0.19,
    depthWrite: false,
    blending: THREE.AdditiveBlending
  })))

  const rings = [
    { rotation: [0.35, 0.12, 0.15], color: 0x55dcec, opacity: 0.17 },
    { rotation: [1.05, 0.25, 0.6], color: 0x8272ef, opacity: 0.13 },
    { rotation: [0.15, 1.15, 0.9], color: 0x4d95e8, opacity: 0.1 }
  ]
  rings.forEach(({ rotation, color, opacity }) => {
    const ring = new THREE.Mesh(
      new THREE.TorusGeometry(radius * 1.09, 0.008, 4, 180),
      new THREE.MeshBasicMaterial({ color, transparent: true, opacity, depthWrite: false })
    )
    ring.rotation.set(...rotation)
    network.add(ring)
  })

  const pulses = [0x9d8aff, 0x70e8f4, 0x5fa8ff].map((color, index) => {
    const pulse = new THREE.Mesh(
      new THREE.SphereGeometry(0.045, 8, 8),
      new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.9 })
    )
    network.add(pulse)
    return { mesh: pulse, edgeIndex: (index * 37) % edges.length, offset: index / 3, edges }
  })

  return { network, pulses }
}

function createParticles(count) {
  const positions = new Float32Array(count * 3)
  for (let index = 0; index < count; index += 1) {
    positions[index * 3] = (Math.random() - 0.5) * 17
    positions[index * 3 + 1] = (Math.random() - 0.5) * 10
    positions[index * 3 + 2] = (Math.random() - 0.5) * 7 - 2
  }

  const geometry = new THREE.BufferGeometry()
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
  const material = new THREE.PointsMaterial({
    color: 0x90dff1,
    size: 0.025,
    transparent: true,
    opacity: 0.48,
    sizeAttenuation: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending
  })
  return new THREE.Points(geometry, material)
}

export default function NeuralBackground() {
  const hostRef = useRef(null)
  const [reducedMotion, setReducedMotion] = useState(() => window.matchMedia(reduceMotionQuery).matches)

  useEffect(() => {
    const mediaQuery = window.matchMedia(reduceMotionQuery)
    const updatePreference = () => setReducedMotion(mediaQuery.matches)
    mediaQuery.addEventListener('change', updatePreference)
    return () => mediaQuery.removeEventListener('change', updatePreference)
  }, [])

  useEffect(() => {
    const host = hostRef.current
    if (!host || reducedMotion) return undefined

    let renderer
    try {
      renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true, powerPreference: 'low-power' })
    } catch {
      return undefined
    }

    const width = window.innerWidth
    const height = window.innerHeight
    const scene = new THREE.Scene()
    const camera = new THREE.PerspectiveCamera(42, width / height, 0.1, 100)
    camera.position.z = 11
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5))
    renderer.setSize(width, height)
    renderer.setClearColor(0x000000, 0)
    renderer.outputColorSpace = THREE.SRGBColorSpace
    renderer.domElement.setAttribute('aria-hidden', 'true')
    host.appendChild(renderer.domElement)

    const nodeCount = Math.max(54, Math.min(148, Math.floor((width * height) / 8500)))
    const { network, pulses } = createNetwork(nodeCount, 3.05)
    network.position.set(width < 700 ? 0.2 : 1.15, 0.05, 0)
    network.scale.setScalar(width < 700 ? 0.76 : 1)
    scene.add(network)

    const particles = createParticles(width < 700 ? 70 : Math.min(230, Math.floor((width * height) / 6000)))
    scene.add(particles)

    let frameId = 0
    let targetRotationX = 0
    let targetRotationY = 0
    let pointerX = 0
    let pointerY = 0
    const onPointerMove = (event) => {
      pointerX = (event.clientX / window.innerWidth - 0.5) * 2
      pointerY = (event.clientY / window.innerHeight - 0.5) * 2
    }
    const onResize = () => {
      const nextWidth = window.innerWidth
      const nextHeight = window.innerHeight
      camera.aspect = nextWidth / nextHeight
      camera.updateProjectionMatrix()
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5))
      renderer.setSize(nextWidth, nextHeight)
      network.position.x = nextWidth < 700 ? 0.2 : 1.15
      network.scale.setScalar(nextWidth < 700 ? 0.76 : 1)
    }

    const animate = (time) => {
      frameId = window.requestAnimationFrame(animate)
      targetRotationX += (pointerY * 0.055 - targetRotationX) * 0.018
      targetRotationY += (pointerX * 0.075 - targetRotationY) * 0.018
      network.rotation.x = targetRotationX + Math.sin(time * 0.00012) * 0.08
      network.rotation.y = time * 0.000045 + targetRotationY
      particles.rotation.y = time * 0.000012
      particles.rotation.x = Math.sin(time * 0.00008) * 0.025

      pulses.forEach(({ mesh, edgeIndex, offset, edges }) => {
        const [start, end] = edges[edgeIndex]
        const progress = (time * 0.00011 + offset) % 1
        mesh.position.lerpVectors(start, end, progress)
      })

      renderer.render(scene, camera)
    }

    window.addEventListener('pointermove', onPointerMove, { passive: true })
    window.addEventListener('resize', onResize)
    frameId = window.requestAnimationFrame(animate)

    return () => {
      window.cancelAnimationFrame(frameId)
      window.removeEventListener('pointermove', onPointerMove)
      window.removeEventListener('resize', onResize)
      scene.traverse((object) => {
        object.geometry?.dispose()
        if (Array.isArray(object.material)) object.material.forEach((material) => material.dispose())
        else object.material?.dispose()
      })
      renderer.dispose()
      renderer.domElement.remove()
    }
  }, [reducedMotion])

  return <div ref={hostRef} className={`neural-background${reducedMotion ? ' neural-background-static' : ''}`} aria-hidden="true" />
}