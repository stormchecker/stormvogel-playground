import fs from 'fs';
import path from 'path';

function loadExamplesFromFiles() {
    const examplesDir = './examples';
    const examples = [];
    
    // Get all subdirectories in the examples folder
    const exampleDirs = fs.readdirSync(examplesDir, { withFileTypes: true })
        .filter(dirent => dirent.isDirectory())
        .map(dirent => dirent.name);
    
    exampleDirs.forEach(dirName => {
        const dirPath = path.join(examplesDir, dirName);
        const files = {};
        
        // Read all files in the directory
        const fileNames = fs.readdirSync(dirPath);
        fileNames.forEach(fileName => {
            const filePath = path.join(dirPath, fileName);
            const fileContent = fs.readFileSync(filePath, 'utf8');
            files[fileName] = fileContent;
        });
        
        examples.push({
            title: dirName.toUpperCase(),
            files: files
        });
    });
    
    return examples;
}

export const examples = loadExamplesFromFiles();
