# Safety Standards Data Sources

**CRITICAL**: This document identifies authoritative sources for OSHA/ANSI safety standards data.
All safety standards in the Horme POV system MUST be sourced from official regulatory and standards organizations.

## OSHA (Occupational Safety and Health Administration)

### Primary Source
- **Official Website**: https://www.osha.gov/
- **Regulations Database**: https://www.osha.gov/laws-regs/regulations/standardnumber
- **Construction Standards (29 CFR 1926)**: https://www.osha.gov/laws-regs/regulations/standardnumber/1926

### Standards Loaded in Database

#### 29 CFR 1926.102 - Eye and Face Protection
- **URL**: https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.102
- **PDF**: https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.102(pdf)
- **Scope**: Requirements for eye and face protection equipment
- **Key Requirements**: ANSI Z87.1-1968 compliance, protection from physical/chemical/radiation hazards
- **Penalties**: Up to $13,653 per violation (2021 rates)

#### 29 CFR 1926.138 - Hand Protection
- **URL**: https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.138
- **Scope**: Requirements for hand protection against cuts, lacerations, chemical burns
- **Key Requirements**: Appropriate hand protection selection based on hazards

#### 29 CFR 1926.96 - Occupational Foot Protection
- **URL**: https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.96
- **Scope**: Protective footwear requirements
- **Key Requirements**: Protection from falling objects, piercing hazards, electrical hazards

#### 29 CFR 1926.100 - Head Protection
- **URL**: https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.100
- **Scope**: Hard hat and head protection requirements
- **Key Requirements**: Protection from impact, falling objects, electrical shock

#### 29 CFR 1926.101 - Hearing Protection
- **URL**: https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.101
- **Scope**: Hearing conservation requirements
- **Key Requirements**: Protection when noise exceeds 85 dBA for 8 hours

#### 29 CFR 1926.103 - Respiratory Protection
- **URL**: https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.103
- **Scope**: Respiratory protective equipment requirements
- **Key Requirements**: Compliance with 29 CFR 1910.134

#### 29 CFR 1926.302 - Power-Operated Hand Tools
- **URL**: https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.302
- **Scope**: Safety requirements for power tools
- **Key Requirements**: Guards, safety devices, operator protection

#### 29 CFR 1926.95 - Criteria for Personal Protective Equipment
- **URL**: https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.95
- **Scope**: General PPE requirements and criteria
- **Key Requirements**: Provision, use, and maintenance of PPE

### How to Update OSHA Data

1. **Visit Official OSHA Website**: Navigate to https://www.osha.gov/laws-regs/regulations
2. **Select Construction Standards (Part 1926)**: https://www.osha.gov/laws-regs/regulations/standardnumber/1926
3. **Review Specific CFR Numbers**: Click on individual standards (e.g., 1926.102)
4. **Extract Official Text**: Copy requirements, penalties, and legal references
5. **Update Database**: Run `scripts/load_safety_standards_postgresql.py` with updated data
6. **Verify Accuracy**: Cross-reference with PDF versions of regulations

## ANSI (American National Standards Institute)

### Primary Source
- **Official Website**: https://www.ansi.org/
- **Standards Store**: https://webstore.ansi.org/

### ANSI Z87.1-2020 - Eye and Face Protection
- **Title**: Occupational and Educational Personal Eye and Face Protection Devices
- **Purchase URL**: https://webstore.ansi.org/standards/isea/ansiz872020
- **Price**: ~$75 USD
- **Key Data**:
  - Basic impact marking: Z87
  - High-impact marking: Z87+
  - Splash/droplet marking: Z87 D3
  - Dust marking: Z87 D4, D5
  - Test requirements: 1/4 inch steel ball at 150 ft/s

### ANSI S3.19-1974 (R2018) - Hearing Protection
- **Title**: Method for the Measurement of Real-Ear Protection of Hearing Protectors
- **Purchase URL**: https://webstore.ansi.org/standards/asa/ansiasas31974r2018
- **Price**: ~$50 USD
- **Key Data**:
  - Noise Reduction Rating (NRR) methodology
  - EPA derating: NRR - 7 dB
  - Noise exposure limits (85-115 dBA)

## ISEA (International Safety Equipment Association)

### Primary Source
- **Official Website**: https://www.isea.org/

### ANSI/ISEA 105-2016 - Hand Protection
- **Title**: American National Standard for Hand Protection Classification
- **Purchase URL**: https://safetyequipment.org/isea-product/ansi-isea-105-2016/
- **Price**: ~$75 USD
- **Key Data**:
  - Cut resistance levels A1-A9
  - TDM-100 test method
  - Puncture resistance levels 1-5
  - Abrasion resistance levels 0-6

### ANSI/ISEA 107-2020 - High-Visibility Apparel
- **Title**: High-Visibility Safety Apparel and Accessories
- **Purchase URL**: https://safetyequipment.org/isea-product/ansi-isea-107-2020/
- **Price**: ~$90 USD
- **Key Data**:
  - Performance classes (Type P, R, O)
  - Background material requirements
  - Retroreflective material specifications

## ASTM International

### Primary Source
- **Official Website**: https://www.astm.org/
- **Standards Store**: https://www.astm.org/products-services/standards-and-publications/standards.html

### ASTM F2413-18 - Protective Footwear
- **Title**: Standard Specification for Performance Requirements for Protective Footwear
- **Purchase URL**: https://www.astm.org/f2413-18.html
- **Price**: ~$65 USD
- **Key Data**:
  - Impact protection: I/75 (75 ft-lbs), I/50 (50 ft-lbs)
  - Compression protection: C/75 (2500 lbs), C/50 (1750 lbs)
  - Metatarsal protection: Mt
  - Puncture resistance: PR (1200 Newtons)
  - Electrical hazard: EH (18,000 volts)
  - Required marking: "ASTM F2413-18 I/75 C/75"

### ASTM Z89.1-2017 - Head Protection
- **Title**: American National Standard for Industrial Head Protection
- **Purchase URL**: https://webstore.ansi.org/standards/isea/ansiz892017
- **Price**: ~$70 USD
- **Key Data**:
  - Type I: Top impact protection
  - Type II: Top and lateral impact protection
  - Class E: Electrical (20,000 volts)
  - Class G: General (2,200 volts)
  - Class C: Conductive (no electrical protection)

## Free Government Resources

### OSHA Publications (Free)
- **OSHA Construction Standards**: https://www.osha.gov/Publications/osha2202.pdf
- **Personal Protective Equipment**: https://www.osha.gov/Publications/osha3151.pdf
- **Respiratory Protection**: https://www.osha.gov/Publications/3384small-entity-for-respiratory-protection-standard-rev.pdf
- **Eye and Face Protection**: https://www.osha.gov/Publications/OSHA3151/osha3151.html

### NIOSH Publications (Free)
- **Hearing Loss Prevention**: https://www.cdc.gov/niosh/topics/noise/default.html
- **Respirator Selection Guide**: https://www.cdc.gov/niosh/docs/2005-100/
- **Personal Protective Equipment**: https://www.cdc.gov/niosh/topics/ppe/

### EPA Resources (Free)
- **Hearing Protection Derating**: https://www.epa.gov/sites/default/files/2018-07/documents/hearing_protection_devices_compendium.pdf

## Data Update Frequency

### Regulatory Updates
- **OSHA CFR Standards**: Check quarterly for updates
  - Subscribe to OSHA updates: https://www.osha.gov/quicktakes/
  - Federal Register notices: https://www.federalregister.gov/agencies/occupational-safety-and-health-administration

### ANSI/ASTM Standards
- **Review Cycle**: Every 5 years
- **Check for Revisions**: Annually
- **Subscribe to Updates**: ANSI Standards Action (weekly publication)

## Implementation in Horme POV

### Database Tables
All data is stored in PostgreSQL with the following schema:

1. **osha_standards** - OSHA CFR standards with requirements
2. **ansi_standards** - ANSI/ISEA/ASTM standards with specifications
3. **tool_risk_classifications** - Tool hazard assessments
4. **task_hazard_mappings** - Task-to-hazard safety mappings
5. **ansi_equipment_specifications** - Equipment certification requirements

### Data Loading Process
```bash
# Run the safety standards loader
python scripts/load_safety_standards_postgresql.py
```

### DataFlow Models
- `OSHAStandard` - Auto-generates 9 CRUD nodes
- `ANSIStandard` - Auto-generates 9 CRUD nodes
- `ToolRiskClassification` - Auto-generates 9 CRUD nodes
- `TaskHazardMapping` - Auto-generates 9 CRUD nodes
- `ANSIEquipmentSpecification` - Auto-generates 9 CRUD nodes

### Compliance Engines
- `OSHAComplianceEngine` - Loads from `osha_standards` table
- `ANSIComplianceEngine` - Loads from `ansi_standards` table

## Legal Disclaimer

The safety standards data in this system is sourced from official government and standards organization publications. However:

1. **Not Legal Advice**: This system provides informational guidance only and does not constitute legal or professional safety advice.

2. **Verify with Originals**: Always verify requirements against official OSHA regulations and ANSI/ASTM standards documents.

3. **Regular Updates Required**: Safety standards are periodically updated. Maintain current versions.

4. **Professional Consultation**: Consult qualified safety professionals and legal counsel for compliance matters.

5. **No Warranty**: This data is provided "as is" without warranty of any kind.

## Contact Information

### OSHA
- **Phone**: 1-800-321-OSHA (6742)
- **Website**: https://www.osha.gov/
- **Regional Offices**: https://www.osha.gov/contactus/bystate

### ANSI
- **Phone**: +1-212-642-4900
- **Email**: info@ansi.org
- **Website**: https://www.ansi.org/

### ISEA
- **Phone**: +1-703-525-1695
- **Email**: isea@safetyequipment.org
- **Website**: https://www.isea.org/

### ASTM International
- **Phone**: +1-610-832-9500
- **Email**: service@astm.org
- **Website**: https://www.astm.org/

## Version History

| Version | Date | Changes | Updated By |
|---------|------|---------|------------|
| 1.0 | 2025-01-17 | Initial data sources documentation | Claude Code |

## Next Review Date
**2025-04-17** (Quarterly review recommended)
