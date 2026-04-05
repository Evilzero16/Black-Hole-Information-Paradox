import numpy as np
import pandas as pd


df = pd.read_csv("/Users/hrishitkotadia/PycharmProjects/Black-Hole-Information-Paradox/data/quantum_state_results.csv")

shots=1000
expected_probabilities = {
    "0": {"0": 1.0, "1": 0.0},
    "1": {"0": 0.0, "1": 1.0},
    "+": {"0": 0.5, "1": 0.5},
    "-": {"0": 0.5, "1": 0.5},
}

def expected_ry(theta):
    return {"0": np.cos(theta / 2) ** 2, "1": np.sin(theta / 2) ** 2}


def calculate_fidelity(expected_probs, measured_counts, shots):
    measured_probs = {key: count / shots for key, count in
                      eval(measured_counts).items()}
    print(measured_probs)

    fidelity = sum(
        np.sqrt(expected_probs.get(key, 0) * measured_probs.get(key, 0)) for key
        in [ "0", "1" ])
    return fidelity


fidelity_results = [ ]

for index, row in df.iterrows():
    state = row[ "State" ]
    theta = row[ "Theta" ]
    measured_counts = row[ "Counts" ]

    if state == "ry":
        if isinstance(theta, str):
            theta = eval(theta.replace("π", "np.pi"))
        else:
            theta = float(theta)
        expected_probs = expected_ry(theta)
    else:
        expected_probs = expected_probabilities[ state ]

    fidelity = calculate_fidelity(expected_probs, measured_counts, shots)

    fidelity_results.append(
        {"State": state, "Theta": row[ "Theta" ], "Fidelity": fidelity})


fidelity_df = pd.DataFrame(fidelity_results)
fidelity_df["Theta"] = fidelity_df["Theta"].apply(lambda x: "N/A" if pd.isna(x) else x)
fidelity_df.to_csv("/Users/hrishitkotadia/PycharmProjects/Black-Hole-Information-Paradox/data/results/fidelity_scores.csv", index=False)

print("✅ Fidelity calculations saved as 'fidelity_scores.csv'")













