const fs = require('fs');
const path = require('path');
const XLSX = require('xlsx');

// Create a new workbook
const workbook = XLSX.utils.book_new();

// Sample data for projects
const sampleData = [
  {
    project_code: "2ES00001",
    project_name: "Sample Project 1",
    portfolio_cluster: "Portfolio A",
    status: 1
  },
  {
    project_code: "2ES00002",
    project_name: "Sample Project 2",
    portfolio_cluster: "Portfolio B",
    status: 1
  },
  {
    project_code: "2ES00003",
    project_name: "Sample Project 3",
    portfolio_cluster: "Portfolio A",
    status: 0
  }
];

// Create a worksheet
const worksheet = XLSX.utils.json_to_sheet(sampleData);

// Add the worksheet to the workbook
XLSX.utils.book_append_sheet(workbook, worksheet, "Projects");

// Write the workbook to a file
const outputPath = path.join(__dirname, '../public/samples/sample-projects.xlsx');
XLSX.writeFile(workbook, outputPath);

console.log(`Sample Excel file created at: ${outputPath}`);
