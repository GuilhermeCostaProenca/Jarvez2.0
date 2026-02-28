const mod = require("../vendor/t20-sheet-builder/build");

function normalize(text) {
  return String(text || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
}

function unique(items) {
  return [...new Set(items.filter(Boolean))];
}

function selectTopAttributes(attributes, count, excluded = []) {
  const entries = Object.entries(attributes || {})
    .filter(([key]) => !excluded.includes(key))
    .sort((a, b) => Number(b[1]) - Number(a[1]));
  return entries.slice(0, count).map(([key]) => key);
}

function normalizeAttributes(rawAttributes) {
  const base = {
    strength: 0,
    dexterity: 0,
    constitution: 0,
    intelligence: 0,
    wisdom: 0,
    charisma: 0,
  };
  const source = rawAttributes && typeof rawAttributes === "object" ? rawAttributes : {};
  const keyMap = {
    forca: "strength",
    força: "strength",
    strength: "strength",
    destreza: "dexterity",
    dexterity: "dexterity",
    constituicao: "constitution",
    constituição: "constitution",
    constitution: "constitution",
    inteligencia: "intelligence",
    inteligência: "intelligence",
    intelligence: "intelligence",
    sabedoria: "wisdom",
    wisdom: "wisdom",
    carisma: "charisma",
    charisma: "charisma",
  };

  const rawValues = [];
  for (const [key, value] of Object.entries(source)) {
    const mapped = keyMap[normalize(key)];
    if (!mapped || typeof value !== "number" || Number.isNaN(value)) {
      continue;
    }
    rawValues.push(value);
    base[mapped] = value;
  }

  const treatAsModifier =
    rawValues.length > 0 && rawValues.every((value) => value >= -5 && value <= 8);
  if (treatAsModifier) {
    return base;
  }

  const converted = {};
  for (const [key, value] of Object.entries(base)) {
    converted[key] = Math.max(-5, Math.min(10, Math.floor((Number(value) - 10) / 2)));
  }
  return converted;
}

function chooseRoleSkills(roleCtor) {
  const groups = Array.isArray(roleCtor.selectSkillGroups) ? roleCtor.selectSkillGroups : [];
  const selections = [];
  for (const group of groups) {
    const skills = Array.isArray(group.skills) ? group.skills : [];
    const amount = Number(group.amount || 0);
    selections.push(unique(skills.slice(0, Math.max(0, amount))));
  }
  return selections;
}

function makeRole(roleName) {
  const normalized = normalize(roleName);
  if (normalized === "arcanista" || normalized === "arcanist" || normalized === "mago" || normalized === "wizard") {
    return {
      ok: false,
      error:
        "Classe 'arcanista' ainda nao esta suportada pela bridge automatica; a engine exige configuracao adicional de magias/circulos. Use fallback por enquanto.",
    };
  }
  const roleMap = {
    guerreiro: mod.Warrior,
    warrior: mod.Warrior,
    barbaro: mod.Barbarian,
    bárbaro: mod.Barbarian,
    barbarian: mod.Barbarian,
    bardo: mod.Bard,
    bard: mod.Bard,
    bucaneiro: mod.Buccaneer,
    buccaneer: mod.Buccaneer,
    cacador: mod.Ranger,
    caçador: mod.Ranger,
    ranger: mod.Ranger,
    cavaleiro: mod.Knight,
    knight: mod.Knight,
    clerigo: mod.Cleric,
    clérigo: mod.Cleric,
    cleric: mod.Cleric,
    druida: mod.Druid,
    druid: mod.Druid,
    inventor: mod.Inventor,
    rogue: mod.Rogue,
    ladino: mod.Rogue,
    lutador: mod.Fighter,
    fighter: mod.Fighter,
    nobre: mod.Noble,
    noble: mod.Noble,
    paladino: mod.Paladin,
    paladin: mod.Paladin,
  };
  const RoleCtor = roleMap[normalized];
  if (!RoleCtor) {
    return {
      ok: false,
      error: `Classe '${roleName}' ainda nao esta suportada pela bridge automatica.`,
    };
  }
  return {
    ok: true,
    role: new RoleCtor(chooseRoleSkills(RoleCtor)),
    resolvedName: normalized,
  };
}

function makeRace(raceName, attributes) {
  const normalized = normalize(raceName);
  const topThree = selectTopAttributes(attributes, 3);
  const defaultVersatileChoices = [
    new mod.VersatileChoiceSkill(mod.SkillName.acrobatics),
    new mod.VersatileChoicePower(new mod.Dodge()),
  ];

  switch (normalized) {
    case "humano":
    case "human":
      return { ok: true, race: new mod.Human(topThree, defaultVersatileChoices) };
    case "anao":
    case "anão":
    case "dwarf":
      return { ok: true, race: new mod.Dwarf() };
    case "dahllan":
      return { ok: true, race: new mod.Dahllan() };
    case "elfo":
    case "elf":
      return { ok: true, race: new mod.Elf() };
    case "goblin":
      return { ok: true, race: new mod.Goblin() };
    case "minotauro":
    case "minotaur":
      return { ok: true, race: new mod.Minotaur() };
    case "lefou":
    case "lefeu": {
      const race = new mod.Lefeu(topThree);
      race.addDeformities([mod.SkillName.fight, mod.SkillName.fortitude]);
      return { ok: true, race };
    }
    case "qareen":
      return { ok: true, race: new mod.Qareen("water", mod.SpellName.arcaneArmor) };
    default:
      return {
        ok: false,
        error: `Raca '${raceName}' ainda nao esta suportada pela bridge automatica.`,
      };
  }
}

function makeOrigin(originName) {
  const normalized = normalize(originName || "acolyte");
  switch (normalized) {
    case "acolyte":
    case "acolito":
    case "acólito":
      return {
        ok: true,
        origin: new mod.Acolyte([
          new mod.OriginBenefitGeneralPower(new mod.IronWill()),
          new mod.OriginBenefitSkill(mod.SkillName.cure),
        ]),
      };
    case "animalsfriend":
    case "animals_friend":
    case "amigo dos animais":
    case "amigo_dos_animais":
      return {
        ok: true,
        origin: new mod.AnimalsFriend([new mod.OriginBenefitSkill(mod.SkillName.animalHandling)]),
      };
    default:
      return {
        ok: false,
        error: `Origem '${originName}' ainda nao esta suportada pela bridge automatica.`,
      };
  }
}

function makeInitialEquipment(resolvedRole) {
  const equipment = {
    simpleWeapon: new mod.Dagger(),
    money: 24,
  };
  if (resolvedRole !== "arcanista" && mod.LeatherArmor) {
    equipment.armor = new mod.LeatherArmor();
  }
  if (mod.LongSword) {
    equipment.martialWeapon = new mod.LongSword();
  }
  return equipment;
}

function buildSummary(serialized) {
  const sheet = serialized.sheet || {};
  const skills = Object.entries(sheet.skills?.skills || {})
    .map(([name, data]) => ({
      name,
      total: data.total,
      trained: Boolean(data.isTrained),
      attribute: data.attribute,
    }))
    .sort((a, b) => Number(b.total) - Number(a.total));

  return {
    builder: "t20-sheet-builder",
    system: "tormenta20-t20-sheet-builder",
    race: sheet.race?.name || null,
    role: sheet.role?.name || null,
    origin: sheet.origin?.name || null,
    level: sheet.level || 1,
    defense: sheet.defense?.total ?? null,
    life_points: sheet.lifePoints?.max ?? null,
    mana_points: sheet.manaPoints?.max ?? null,
    attributes: sheet.attributes || {},
    trained_skills: skills.filter((item) => item.trained).slice(0, 12),
    top_skills: skills.slice(0, 12),
    attacks: Array.isArray(serialized.attacks) ? serialized.attacks : [],
    build_steps: Array.isArray(sheet.buildSteps) ? sheet.buildSteps : [],
    serialized_character: serialized,
  };
}

function main() {
  try {
    const rawInput = require("fs").readFileSync(0, "utf8");
    const payload = JSON.parse(rawInput || "{}");
    const attributes = normalizeAttributes(payload.attributes);
    const raceResult = makeRace(payload.race || "humano", attributes);
    if (!raceResult.ok) {
      process.stdout.write(JSON.stringify({ success: false, error: raceResult.error }));
      return;
    }
    const roleResult = makeRole(payload.class_name || "guerreiro");
    if (!roleResult.ok) {
      process.stdout.write(JSON.stringify({ success: false, error: roleResult.error }));
      return;
    }
    const originResult = makeOrigin(payload.origin || "acolyte");
    if (!originResult.ok) {
      process.stdout.write(JSON.stringify({ success: false, error: originResult.error }));
      return;
    }

    const builder = new mod.default();
    const sheet = builder
      .setInitialAttributes(attributes)
      .chooseRace(raceResult.race)
      .chooseRole(roleResult.role)
      .chooseOrigin(originResult.origin)
      .trainIntelligenceSkills([])
      .addInitialEquipment(makeInitialEquipment(roleResult.resolvedName))
      .build();
    const character = new mod.Character(sheet);
    const serialized = character.serialize();

    process.stdout.write(
      JSON.stringify({
        success: true,
        data: buildSummary(serialized),
      }),
    );
  } catch (error) {
    process.stdout.write(
      JSON.stringify({
        success: false,
        error: error instanceof Error ? error.message : String(error),
      }),
    );
  }
}

main();
