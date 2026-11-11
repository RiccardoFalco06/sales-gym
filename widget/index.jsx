// Sales Gym: mostra i pannelli generati da ~/Projects/sales-gym. Si ricarica solo quando i dati cambiano,
// così l'animazione riparte a ogni video e non ogni minuto.
import { React } from "uebersicht";

export const command = "cat sales-gym.widget/version.txt";
export const refreshFrequency = 60000;
export const className = `
  /* colonna a sinistra, prima delle icone: scelta di Riccardo */
  left: 20px; top: 44px;
  display: grid; grid-template-columns: 290px; gap: 10px;
  img { width: 290px; display: block; }
`;
const panels = ["calendario", "voto", "ultima"]; // gli altri pannelli sono nella dashboard di Obsidian
export const render = ({ output }) => {
  const v = encodeURIComponent((output || "").trim());
  return <>{panels.map(p => <img key={p + v} src={`sales-gym.widget/${p}.svg?v=${v}`} />)}</>;
};
