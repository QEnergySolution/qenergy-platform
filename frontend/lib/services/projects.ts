// Mocked service adapter for Phase 1: returns the same data shape the UI expects

export interface UiProject {
  id: string;
  code: string;
  name: string;
  portfolio: string;
  active: boolean;
}

const mockedProjects: UiProject[] = [
  { id: "1", code: "2ES00009", name: "Boedo 1", portfolio: "Herrera", active: true },
  { id: "2", code: "2ES00010", name: "Boedo 2", portfolio: "Herrera", active: true },
  { id: "3", code: "2DE00001", name: "Illmersdorf", portfolio: "Illmersdorf", active: true },
  { id: "4", code: "2DE00002", name: "Garwitz", portfolio: "Lunaco", active: false },
  { id: "5", code: "2DE00003", name: "Matzlow", portfolio: "Lunaco", active: true },
  { id: "6", code: "2DE00004", name: "IM 24 Tangerhütte", portfolio: "Aristoteles_1", active: true },
  { id: "7", code: "IM 07 Blankensee", name: "IM 07 Blankensee", portfolio: "Aristoteles_2", active: false },
  { id: "8", code: "IM 44 Gondorf", name: "IM 44 Gondorf", portfolio: "Aristoteles_3", active: true },
  { id: "9", code: "2DE00007", name: "Letzendorf", portfolio: "Advice2Energy", active: true },
  { id: "10", code: "2DE00013", name: "Bosseborn_2", portfolio: "Bosseborn_2", active: true },
  { id: "11", code: "2DE00015", name: "Wethen", portfolio: "Wethen", active: false },
  { id: "12", code: "2DE00016", name: "Oberndorf", portfolio: "Oberndorf", active: true },
  { id: "13", code: "IM 16 Bad Freienwalde", name: "IM 16 Bad Freienwalde", portfolio: "Aristoteles_2", active: true },
  { id: "14", code: "IM 37 Barnim", name: "IM 37 Barnim", portfolio: "Aristoteles_2", active: true },
  { id: "15", code: "Dahlen", name: "Dahlen", portfolio: "Dahlen", active: false },
  { id: "16", code: "IM 18 Reichenberg", name: "IM 18 Reichenberg", portfolio: "Aristoteles_2", active: true },
  { id: "17", code: "2ES00007", name: "Cabrovales 1", portfolio: "Cabrovales 1", active: true },
  { id: "18", code: "2ES00011", name: "Torozos 1", portfolio: "Zaratan_PV", active: true },
  { id: "19", code: "2ES00012", name: "Torozos 2", portfolio: "Zaratan_PV", active: true },
  { id: "20", code: "2ES00013", name: "Torozos 3", portfolio: "Zaratan_PV", active: true },
];

export async function fetchProjects(): Promise<UiProject[]> {
  // Simulate async API call
  await new Promise((r) => setTimeout(r, 10));
  return mockedProjects;
}


