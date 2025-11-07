// Vite Worker Module Declarations
// These declarations tell TypeScript that importing with ?worker suffix is valid

declare module '*?worker' {
  const WorkerFactory: new () => Worker;
  export default WorkerFactory;
}

declare module '*?worker&inline' {
  const WorkerFactory: new () => Worker;
  export default WorkerFactory;
}
