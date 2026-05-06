# Synthetic Data

Public demos for this repository use synthetic data only. Do not place real private policy documents, client files, employer data, confidential records, or production exports in this directory.

> This project uses synthetic data for educational and portfolio demonstration purposes. It does not contain private customer data, employer data, confidential records, or production exports.

## Policy Packet

The policy brief MVP includes a synthetic packet at `data/synthetic/policy_packet/`. The packet uses one coherent fictional topic: local housing affordability and zoning reform in the City of Riverton. Each document is clearly marked as synthetic and is safe for public demos.

Current packet files:

- `policy_packet/01_city_housing_needs_memo.md`
- `policy_packet/02_zoning_reform_options.md`
- `policy_packet/03_community_feedback_summary.md`
- `policy_packet/04_implementation_timeline.md`

## Windows Setup Note

Use PowerShell-compatible commands from the repository root when exploring the packet locally:

```powershell
Get-ChildItem .\data\synthetic\policy_packet
Get-Content .\data\synthetic\policy_packet\01_city_housing_needs_memo.md
```
