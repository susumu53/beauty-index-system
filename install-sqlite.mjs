// better-sqlite3 の Windows x64 プリビルドバイナリをダウンロードして配置するスクリプト
import https from 'https';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { createGunzip } from 'zlib';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Node.js の NAPI バージョンを確認
const napiVersions = {
  '24': 9,
  '23': 9,
  '22': 9,
  '21': 9,
  '20': 9,
  '18': 8,
};

const nodeMajor = parseInt(process.version.slice(1).split('.')[0], 10);
const napi = napiVersions[String(nodeMajor)] ?? 9;

const pkg = JSON.parse(fs.readFileSync(
  path.join(__dirname, 'node_modules/better-sqlite3/package.json'), 'utf8'
));
const version = pkg.version;

// better-sqlite3 の GitHub Releases URL パターン
const fileName = `better-sqlite3-v${version}-napi-v${napi}-win32-x64.tar.gz`;
const url = `https://github.com/WiseLibs/better-sqlite3/releases/download/v${version}/${fileName}`;

const prebuildDir = path.join(__dirname, 'node_modules/better-sqlite3/prebuilds/win32-x64');
const destFile = path.join(__dirname, `tmp_${fileName}`);

console.log(`ダウンロード: ${url}`);
console.log(`Node.js ${process.version} (NAPI v${napi})`);

fs.mkdirSync(prebuildDir, { recursive: true });

function download(url, dest) {
  return new Promise((resolve, reject) => {
    function get(url) {
      https.get(url, (res) => {
        if (res.statusCode === 301 || res.statusCode === 302) {
          get(res.headers.location);
          return;
        }
        if (res.statusCode !== 200) {
          reject(new Error(`HTTP ${res.statusCode}`));
          return;
        }
        const stream = fs.createWriteStream(dest);
        res.pipe(stream);
        stream.on('finish', resolve);
        stream.on('error', reject);
      }).on('error', reject);
    }
    get(url);
  });
}

try {
  await download(url, destFile);
  console.log('ダウンロード完了。解凍中...');

  // tar.gz を解凍（Node.js 組み込みの tar は使えないので node の tar モジュール利用）
  // tar コマンドがある場合はそちらを使う
  const { execSync } = await import('child_process');
  execSync(`tar -xzf "${destFile}" -C "${prebuildDir}"`, { stdio: 'inherit' });
  fs.unlinkSync(destFile);
  console.log('✅ better-sqlite3 プリビルドバイナリを配置しました');
  console.log(`配置先: ${prebuildDir}`);
} catch (e) {
  console.error('❌ エラー:', e.message);
  console.log('\n代替手段: Visual Studio Build Toolsをインストールしてください');
  console.log('  https://visualstudio.microsoft.com/ja/visual-cpp-build-tools/');
  process.exit(1);
}
