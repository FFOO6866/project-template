// Test the formatFileName function
function formatFileName(fileName) {
  // Remove duplicate RFQ_ prefix (e.g., RFQ_RFQ_... → RFQ_...)
  let cleaned = fileName.replace(/^RFQ_RFQ_/i, 'RFQ_')

  // Remove other common duplicate patterns
  cleaned = cleaned.replace(/^RFP_RFP_/i, 'RFP_')
  cleaned = cleaned.replace(/^Quote_Quote_/i, 'Quote_')

  return cleaned
}

// Test cases
const testCases = [
  'RFQ_RFQ_202510_1927_Silverline_Facilities_Group.pdf',
  'RFP_RFP_test_document.pdf',
  'Quote_Quote_12345.pdf',
  'RFQ_normal_file.pdf'
]

console.log('Testing formatFileName function:')
testCases.forEach(test => {
  const result = formatFileName(test)
  console.log(`  Input:  ${test}`)
  console.log(`  Output: ${result}`)
  console.log()
})
