// Placeholder for the 3D avatar renderer.
//
// AvatarRenderer.svelte dynamically imports this module and expects an
// `AvatarRenderer` class with the interface below. The real three.js
// implementation (loading static/avatar/*.glb) was never committed to this
// repo; this no-op keeps the dynamic import resolvable so the app runs. The
// avatar panel simply renders empty until a real renderer is dropped in here.

export class AvatarRenderer {
	private container: HTMLElement;

	constructor(container: HTMLElement) {
		this.container = container;
	}

	async initialize(): Promise<void> {
		// no-op: real renderer would build a three.js scene in this.container
	}

	dispose(): void {
		// no-op: real renderer would release three.js resources here
	}
}
