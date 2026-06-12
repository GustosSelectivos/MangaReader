/* eslint-disable */
const fs = require('fs');
const path = require('path');

function walkDir(dir, callback) {
  fs.readdirSync(dir).forEach(f => {
    let dirPath = path.join(dir, f);
    let isDirectory = fs.statSync(dirPath).isDirectory();
    isDirectory ? walkDir(dirPath, callback) : callback(path.join(dir, f));
  });
}

walkDir(path.join(__dirname, 'src'), function(filePath) {
  if (filePath.endsWith('.vue') || filePath.endsWith('.js')) {
    let content = fs.readFileSync(filePath, 'utf8');
    // regex to replace catch (e) or catch(e) or catch(err) or catch (err) with catch
    let newContent = content.replace(/catch\s*\(\s*[a-zA-Z0-9_]+\s*\)/g, 'catch');
    if (content !== newContent) {
      fs.writeFileSync(filePath, newContent, 'utf8');
      console.log('Updated: ' + filePath);
    }
  }
});
