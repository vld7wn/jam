import {spawnSync} from 'node:child_process'
// Limit native bundler workers on memory-constrained development machines.
const result=spawnSync(process.execPath,['node_modules/vite/bin/vite.js','build'],{
 cwd:new URL('../',import.meta.url),stdio:'inherit',env:{...process.env,RAYON_NUM_THREADS:'1'},
})
if(result.error)console.error(result.error)
process.exit(result.status??1)
