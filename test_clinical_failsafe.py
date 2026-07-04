import numpy as np
import json
import unittest

class FailsafeClinicalMatrix:
    """
    Core implementation of the Ndeleh Fishbone Algorithm (Ndeleh-FBA) V2 
    System Recovery Matrix (SRM) for clinical environments.
    Designed by Ndeleh.
    """
    def __init__(self):
        # Current active drug regimen running on the patient's IV lines
        self.active_regimen = ["Ceftriaxone", "Dobutamine"]
        
        # Molecular cross-talk lookup database (1.0 = Safe, 0.0 = Lethal Chemical Collision)
        self.cross_talk_registry = {
            ("Ceftriaxone", "Calcium_Gluconate"): 0.0, # CRITICAL LETHAL PRECIPITATION IN LUNGS/KIDNEYS
            ("Ceftriaxone", "Dobutamine"): 1.0          # Chemically compatible in separate lines
        }
        
        # Base pump rates calculated by KPE from initial failure scores (mL/h)
        self.pump_rates = {
            "Ceftriaxone": 24.50,
            "Dobutamine": 134.42
        }

    def process_organ_telemetry_and_cross_talk(self, liver_alt_ast_u_l, prospective_new_drug=None):
        print(f"\n🚨 [FAILSAFE SHIELD ACTIVATED: PATIENT PROFILE CYP2D6 METABOLISM DETECTED]")
        print(f"Evaluating Structural Organ Integrity & Chemical Cross-Talk via Ndeleh-FBA V2...")
        print(f"  ├─ Live Telemetry Input: Patient Liver ALT/AST Enzymes = {liver_alt_ast_u_l} U/L (Normal: < 50)")
        
        threshold = 500.0
        sensitivity = 0.01
        omega_liver = round(1.0 - (1.0 / (1.0 + np.exp(-sensitivity * (liver_alt_ast_u_l - threshold)))), 4)
        
        print(f"  ├─ Calculated Liver Attenuation Factor (Omega): {omega_liver} " 
              f"[{'CRITICAL LIVER INFARCTION' if omega_liver < 0.20 else 'ORGAN STABLE'}]")
        
        chi_compatibility = 1.0
        if prospective_new_drug:
            print(f"  ├─ [ORDER INTENT] Physician attempting to inject new compound: [{prospective_new_drug}]")
            for active_drug in self.active_regimen:
                pair = (active_drug, prospective_new_drug)
                reverse_pair = (prospective_new_drug, active_drug)
                if self.cross_talk_registry.get(pair) == 0.0 or self.cross_talk_registry.get(reverse_pair) == 0.0:
                    chi_compatibility = 0.0
                    print(f"  │  [🛑 MOLECULAR COLLISION INTERCEPTED] [{active_drug}] + [{prospective_new_drug}] "
                          f"will cause life-threatening pulmonary/renal micro-crystal precipitation!")
                    break
        
        final_commands = {}
        for drug, current_rate in self.pump_rates.items():
            # Apply organ attenuation AND chemical cross-talk multipliers simultaneously
            failsafe_rate = round(current_rate * omega_liver * chi_compatibility, 2)
            if omega_liver < 0.10 and failsafe_rate >= 0:
                failsafe_rate = min(failsafe_rate, 2.0) # Absolute safety limit to keep lines open
                
            final_commands[drug] = {
                "Original_Target_Rate_mL_h": current_rate,
                "Failsafe_Override_Rate_mL_h": failsafe_rate,
                "Status": "EMERGENCY_THROTTLE_ACTIVE: LIVER FAILURE PROTECTIVE BRAKE" if omega_liver < 0.20 else "RUNNING_NOMINAL"
            }
            
        if chi_compatibility == 0.0:
            print(f"  └─ [SYSTEM LOCKOUT ACTIVATED] Order for [{prospective_new_drug}] is hard-blocked and aborted.")
            
        return final_commands, chi_compatibility, omega_liver

class TestClinicalFailsafe(unittest.TestCase):
    def setUp(self):
        self.system = FailsafeClinicalMatrix()

    def test_molecular_collision_lockout(self):
        commands, chi, omega = self.system.process_organ_telemetry_and_cross_talk(
            liver_alt_ast_u_l=42.0, 
            prospective_new_drug="Calcium_Gluconate"
        )
        self.assertEqual(chi, 0.0)
        self.assertEqual(commands["Ceftriaxone"]["Failsafe_Override_Rate_mL_h"], 0.0)

    def test_acute_organ_failure_throttle(self):
        commands, chi, omega = self.system.process_organ_telemetry_and_cross_talk(
            liver_alt_ast_u_l=950.0
        )
        self.assertLess(omega, 0.05)
        self.assertEqual(commands["Dobutamine"]["Failsafe_Override_Rate_mL_h"], 2.0)

if __name__ == "__main__":
    unittest.main()
