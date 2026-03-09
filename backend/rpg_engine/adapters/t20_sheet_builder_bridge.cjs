const mod = require("../../vendor/t20-sheet-builder/build");
const { Assegai } = require("../../vendor/t20-sheet-builder/build/domain/entities/Inventory/Equipment/Weapon/OffensiveWeapon/SimpleWeapon/Assegai");
const { Accurate } = require("../../vendor/t20-sheet-builder/build/domain/entities/Inventory/Equipment/EquipmentImprovement/Accurate");
const { Acid } = require("../../vendor/t20-sheet-builder/build/domain/entities/Inventory/Equipment/EquipmentAlchemic/Prepared/Acid");
const { LoveElixir } = require("../../vendor/t20-sheet-builder/build/domain/entities/Inventory/Equipment/EquipmentAlchemic/Prepared/LoveElixir");

const SKILL_NAMES = new Set(Object.values(mod.SkillName || {}));
const GENERAL_POWER_MAP = {
  dodge: () => new mod.Dodge(),
  ironwill: () => new mod.IronWill(),
  iron_will: () => new mod.IronWill(),
  medicine: () => new mod.Medicine(),
};
const EQUIPMENT_MAP = {
  dagger: mod.Dagger,
  longsword: mod.LongSword,
  long_sword: mod.LongSword,
  leatherarmor: mod.LeatherArmor,
  leather_armor: mod.LeatherArmor,
};
const MARTIAL_STARTER_ROLES = new Set([
  "guerreiro",
  "warrior",
  "barbaro",
  "barbarian",
  "bucaneiro",
  "buccaneer",
  "cacador",
  "ranger",
  "cavaleiro",
  "knight",
  "lutador",
  "fighter",
  "paladino",
  "paladin",
]);

function normalize(text) {
  return String(text || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
}

function unique(items) {
  return [...new Set((items || []).filter(Boolean))];
}

function isObject(value) {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function fail(message) {
  return { ok: false, error: message };
}

function ok(data) {
  return { ok: true, ...data };
}

function normalizeAbilityName(name) {
  const key = normalize(name);
  const aliases = {
    forca: "strength",
    strength: "strength",
    destreza: "dexterity",
    dexterity: "dexterity",
    constituicao: "constitution",
    constitution: "constitution",
    inteligencia: "intelligence",
    intelligence: "intelligence",
    sabedoria: "wisdom",
    wisdom: "wisdom",
    carisma: "charisma",
    charisma: "charisma",
  };
  return aliases[key] || null;
}

function selectTopAttributes(attributes, count, excluded = []) {
  return Object.entries(attributes || {})
    .filter(([key]) => !excluded.includes(key))
    .sort((a, b) => Number(b[1]) - Number(a[1]))
    .slice(0, count)
    .map(([key]) => key);
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
  const source = isObject(rawAttributes) ? rawAttributes : {};
  const rawValues = [];
  for (const [key, value] of Object.entries(source)) {
    const mapped = normalizeAbilityName(key);
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

function normalizeSkillName(name, allowedSkills = null) {
  const key = normalize(name);
  const direct = Object.values(mod.SkillName || {}).find((skill) => normalize(skill) === key);
  if (!direct) {
    return null;
  }
  if (Array.isArray(allowedSkills) && !allowedSkills.includes(direct)) {
    return null;
  }
  return direct;
}

function resolveRequestedSkills(availableSkills, requestedSkills, amount, strict, label, warnings, avoidSkills = []) {
  const requested = Array.isArray(requestedSkills) ? requestedSkills : [];
  const resolved = [];
  for (const item of requested) {
    const skill = normalizeSkillName(item, availableSkills);
    if (!skill) {
      return fail(`${label}: pericia invalida '${item}'.`);
    }
    if (avoidSkills.includes(skill)) {
      return fail(`${label}: pericia '${item}' ja foi treinada por outra escolha anterior.`);
    }
    if (!resolved.includes(skill)) {
      resolved.push(skill);
    }
    if (resolved.length >= amount) {
      break;
    }
  }

  if (resolved.length >= amount) {
    return ok({ values: resolved.slice(0, amount), autoSelected: false });
  }
  if (strict) {
    return fail(`${label}: informe ${amount} pericias validas.`);
  }

  const autoFilled = [...resolved];
  for (const skill of availableSkills) {
    if (!autoFilled.includes(skill) && !avoidSkills.includes(skill)) {
      autoFilled.push(skill);
    }
    if (autoFilled.length >= amount) {
      break;
    }
  }
  if (autoFilled.length < amount) {
    return fail(`${label}: nao foi possivel completar as pericias automaticamente.`);
  }
  warnings.push(`${label} was auto-selected`);
  return ok({ values: autoFilled, autoSelected: true });
}

function chooseRoleSkills(roleCtor, buildChoices, strict, warnings, avoidSkills = []) {
  const groups = Array.isArray(roleCtor.selectSkillGroups) ? roleCtor.selectSkillGroups : [];
  const requested = Array.isArray(buildChoices?.role_skill_choices) ? buildChoices.role_skill_choices : [];
  const selections = [];
  const applied = [];

  for (let index = 0; index < groups.length; index += 1) {
    const group = groups[index];
    const skills = Array.isArray(group.skills) ? group.skills : [];
    const amount = Math.max(0, Number(group.amount || 0));
    const requestedGroup = Array.isArray(requested[index]) ? requested[index] : [];
    const result = resolveRequestedSkills(
      skills,
      requestedGroup,
      amount,
      strict,
      `role skill group ${index + 1}`,
      warnings,
      avoidSkills,
    );
    if (!result.ok) {
      return result;
    }
    selections.push(unique(result.values));
    applied.push(unique(result.values));
  }

  return ok({ selections, applied });
}

function computePostRaceIntelligence(attributes, raceName, raceAppliedChoices) {
  let intelligence = Number(attributes?.intelligence || 0);
  const normalizedRace = normalize(raceName);
  if (
    (normalizedRace === "humano" || normalizedRace === "human") &&
    Array.isArray(raceAppliedChoices?.attributes) &&
    raceAppliedChoices.attributes.includes("intelligence")
  ) {
    intelligence += 1;
  }
  return intelligence;
}

function flattenRoleSkills(selectedByGroup) {
  const flattened = [];
  for (const group of selectedByGroup || []) {
    for (const skill of group || []) {
      if (!flattened.includes(skill)) {
        flattened.push(skill);
      }
    }
  }
  return flattened;
}

function resolveRogueSpecialistSkills(roleCtor, selectedByGroup, buildChoices, strict, warnings, context) {
  const roleOptions = isObject(buildChoices?.role_options) ? buildChoices.role_options : {};
  const requested = Array.isArray(roleOptions.specialist_skills) ? roleOptions.specialist_skills : [];
  const postRaceIntelligence = computePostRaceIntelligence(
    context?.attributes,
    context?.raceName,
    context?.raceAppliedChoices,
  );
  const required = Math.max(1, postRaceIntelligence > 0 ? postRaceIntelligence : 0);
  const trainedPool = unique([
    ...(Array.isArray(roleCtor.mandatorySkills) ? roleCtor.mandatorySkills : []),
    ...flattenRoleSkills(selectedByGroup),
  ]);

  const resolved = [];
  for (const item of requested) {
    const skill = normalizeSkillName(item, trainedPool);
    if (!skill) {
      return fail(`Rogue exige specialist_skills treinadas e validas; valor invalido '${item}'.`);
    }
    if (!resolved.includes(skill)) {
      resolved.push(skill);
    }
  }

  if (resolved.length < required) {
    if (strict) {
      return fail(`Rogue exige ${required} specialist_skills validas em modo strict.`);
    }
    for (const skill of trainedPool) {
      if (!resolved.includes(skill)) {
        resolved.push(skill);
      }
      if (resolved.length >= required) {
        break;
      }
    }
    warnings.push("rogue specialist skills were auto-selected");
  }

  if (resolved.length < required) {
    return fail("Nao foi possivel resolver specialist_skills para rogue.");
  }

  return ok({
    specialistSkills: new Set(resolved.slice(0, required)),
    appliedChoices: {
      specialist_skills: resolved.slice(0, required),
    },
  });
}

function resolveInventorPrototype(buildChoices, strict, warnings) {
  const roleOptions = isObject(buildChoices?.role_options) ? buildChoices.role_options : {};
  const prototypeChoiceRaw = String(roleOptions.prototype_choice || "").trim();
  const prototypeChoice = prototypeChoiceRaw || (strict ? "" : "superiorItem");

  if (!prototypeChoice) {
    return fail("Inventor exige role_options.prototype_choice em modo strict.");
  }
  if (!prototypeChoiceRaw) {
    warnings.push("inventor prototype was auto-selected");
  }

  const normalizedChoice = normalize(prototypeChoice);
  if (normalizedChoice === "superioritem" || normalizedChoice === "superior_item") {
    const superiorItemMap = {
      assegai: () => new Assegai(),
      dagger: () => new mod.Dagger(),
      longsword: () => new mod.LongSword(),
      long_sword: () => new mod.LongSword(),
    };
    const prototypeItemRaw = String(roleOptions.prototype_item || "").trim();
    const prototypeItemKey = normalize(prototypeItemRaw || (strict ? "" : "assegai"));
    if (!prototypeItemKey || !superiorItemMap[prototypeItemKey]) {
      return fail("Inventor exige role_options.prototype_item valido para superiorItem.");
    }
    if (!prototypeItemRaw) {
      warnings.push("inventor superior item was auto-selected");
    }

    const prototypeImprovementRaw = String(roleOptions.prototype_improvement || "").trim();
    const prototypeImprovementKey = normalize(prototypeImprovementRaw || (strict ? "" : "accurate"));
    if (prototypeImprovementKey !== "accurate") {
      return fail("Inventor suporta apenas role_options.prototype_improvement 'accurate'.");
    }
    if (!prototypeImprovementRaw) {
      warnings.push("inventor superior item improvement was auto-selected");
    }

    return ok({
      prototypeParams: {
        choice: "superiorItem",
        equipment: superiorItemMap[prototypeItemKey](),
        improvement: new Accurate(),
      },
      appliedChoices: {
        prototype_choice: "superiorItem",
        prototype_item: prototypeItemKey === "long_sword" ? "longsword" : prototypeItemKey,
        prototype_improvement: "accurate",
      },
    });
  }

  if (normalizedChoice === "alchemicitems" || normalizedChoice === "alchemic_items") {
    const alchemicMap = {
      acid: Acid,
      loveelixir: LoveElixir,
      love_elixir: LoveElixir,
    };
    const alchemicRaw = String(roleOptions.prototype_alchemic || "").trim();
    const alchemicKey = normalize(alchemicRaw || (strict ? "" : "acid"));
    const AlchemicCtor = alchemicMap[alchemicKey];
    if (!alchemicKey || !AlchemicCtor) {
      return fail("Inventor exige role_options.prototype_alchemic valido para alchemicItems.");
    }
    if (!alchemicRaw) {
      warnings.push("inventor alchemic item was auto-selected");
    }

    const sampleItem = new AlchemicCtor();
    const maxQuantity = Math.max(1, Math.min(10, Math.floor(500 / Number(sampleItem.price || 0 || 1))));
    const explicitQuantity = Number(roleOptions.prototype_quantity);
    const quantity = Number.isFinite(explicitQuantity) && explicitQuantity > 0
      ? Math.floor(explicitQuantity)
      : strict
        ? 0
        : maxQuantity;
    if (quantity <= 0) {
      return fail("Inventor exige role_options.prototype_quantity positivo para alchemicItems em modo strict.");
    }
    if (quantity > maxQuantity) {
      return fail(`Inventor excede o limite de T$500 para '${alchemicKey}'. Quantidade maxima: ${maxQuantity}.`);
    }
    if (!Number.isFinite(explicitQuantity) || explicitQuantity <= 0) {
      warnings.push("inventor alchemic quantity was auto-selected");
    }

    return ok({
      prototypeParams: {
        choice: "alchemicItems",
        alchemicItems: Array.from({ length: quantity }, () => new AlchemicCtor()),
      },
      appliedChoices: {
        prototype_choice: "alchemicItems",
        prototype_item: alchemicKey === "love_elixir" ? "loveelixir" : alchemicKey,
        prototype_quantity: quantity,
      },
    });
  }

  return fail("Inventor suporta apenas prototype_choice 'superiorItem' ou 'alchemicItems'.");
}

function makeRole(roleName, buildChoices, strict, warnings, context = {}) {
  const normalized = normalize(roleName);
  if (normalized === "arcanista" || normalized === "arcanist" || normalized === "mago" || normalized === "wizard") {
    return fail(
      "Classe 'arcanista' ainda nao esta suportada pela bridge automatica; a engine exige configuracao adicional de magias/circulos.",
    );
  }
  const roleMap = {
    guerreiro: mod.Warrior,
    warrior: mod.Warrior,
    barbaro: mod.Barbarian,
    barbarian: mod.Barbarian,
    bardo: mod.Bard,
    bard: mod.Bard,
    bucaneiro: mod.Buccaneer,
    buccaneer: mod.Buccaneer,
    cacador: mod.Ranger,
    ranger: mod.Ranger,
    cavaleiro: mod.Knight,
    knight: mod.Knight,
    clerigo: mod.Cleric,
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
    return fail(`Classe '${roleName}' ainda nao esta suportada pela bridge automatica.`);
  }

  const avoidSkills = [];
  if (context?.raceAppliedChoices?.versatile_skill) {
    avoidSkills.push(context.raceAppliedChoices.versatile_skill);
  }

  const skillChoice = chooseRoleSkills(RoleCtor, buildChoices, strict, warnings, avoidSkills);
  if (!skillChoice.ok) {
    return skillChoice;
  }

  let roleOptionsApplied = {};
  let roleInstance;
  try {
    if (normalized === "inventor") {
      const prototypeResult = resolveInventorPrototype(buildChoices, strict, warnings);
      if (!prototypeResult.ok) {
        return prototypeResult;
      }
      roleOptionsApplied = prototypeResult.appliedChoices;
      roleInstance = new RoleCtor(skillChoice.selections, prototypeResult.prototypeParams);
    } else if (normalized === "rogue" || normalized === "ladino") {
      const specialistResult = resolveRogueSpecialistSkills(
        RoleCtor,
        skillChoice.selections,
        buildChoices,
        strict,
        warnings,
        context,
      );
      if (!specialistResult.ok) {
        return specialistResult;
      }
      roleOptionsApplied = specialistResult.appliedChoices;
      roleInstance = new RoleCtor(skillChoice.selections, specialistResult.specialistSkills);
    } else {
      roleInstance = new RoleCtor(skillChoice.selections);
    }

    return ok({
      role: roleInstance,
      resolvedName: normalized,
      appliedChoices: {
        role_skill_choices: skillChoice.applied,
        role_options: roleOptionsApplied,
      },
    });
  } catch (error) {
    return fail(error instanceof Error ? error.message : String(error));
  }
}

function resolveGeneralPower(name) {
  const factory = GENERAL_POWER_MAP[normalize(name)];
  return factory ? factory() : null;
}

function makeHumanRace(attributes, raceChoices, strict, warnings) {
  const choices = isObject(raceChoices) ? raceChoices : {};
  const requestedAttributes = Array.isArray(choices.attributes) ? choices.attributes : [];
  const normalizedAttributes = [];
  for (const item of requestedAttributes) {
    const mapped = normalizeAbilityName(item);
    if (!mapped) {
      return fail(`race_choices.attributes possui atributo invalido '${item}'.`);
    }
    if (!normalizedAttributes.includes(mapped)) {
      normalizedAttributes.push(mapped);
    }
  }
  const finalAttributes = normalizedAttributes.length >= 3
    ? normalizedAttributes.slice(0, 3)
    : strict
      ? null
      : unique([...normalizedAttributes, ...selectTopAttributes(attributes, 3, normalizedAttributes)]).slice(0, 3);
  if (!finalAttributes || finalAttributes.length < 3) {
    return fail("Humano exige race_choices.attributes com 3 atributos em modo strict.");
  }
  if (normalizedAttributes.length < 3) {
    warnings.push("human race attribute choices were auto-selected");
  }

  const versatileSkill = choices.versatile_skill
    ? normalizeSkillName(choices.versatile_skill)
    : strict
      ? null
      : mod.SkillName.acrobatics;
  if (!versatileSkill) {
    return fail("Humano exige race_choices.versatile_skill valida em modo strict.");
  }
  if (!choices.versatile_skill) {
    warnings.push("human versatile skill was auto-selected");
  }

  const versatilePower = choices.versatile_power
    ? resolveGeneralPower(choices.versatile_power)
    : strict
      ? null
      : new mod.Dodge();
  if (!versatilePower) {
    return fail("Humano exige race_choices.versatile_power valida em modo strict.");
  }
  if (!choices.versatile_power) {
    warnings.push("human versatile power was auto-selected");
  }

  return ok({
    race: new mod.Human(
      finalAttributes,
      [
        new mod.VersatileChoiceSkill(versatileSkill),
        new mod.VersatileChoicePower(versatilePower),
      ],
    ),
    appliedChoices: {
      attributes: finalAttributes,
      versatile_skill: versatileSkill,
      versatile_power: versatilePower.name || versatilePower.constructor.name,
    },
  });
}

function makeLefeuRace(attributes, raceChoices, strict, warnings) {
  const choices = isObject(raceChoices) ? raceChoices : {};
  const requested = Array.isArray(choices.deformities) ? choices.deformities : [];
  const resolved = [];
  for (const item of requested) {
    const skill = normalizeSkillName(item);
    if (!skill) {
      return fail(`race_choices.deformities possui pericia invalida '${item}'.`);
    }
    if (!resolved.includes(skill)) {
      resolved.push(skill);
    }
  }
  const finalDeformities = resolved.length >= 2
    ? resolved.slice(0, 2)
    : strict
      ? null
      : unique([...resolved, mod.SkillName.fight, mod.SkillName.fortitude]).slice(0, 2);
  if (!finalDeformities || finalDeformities.length < 2) {
    return fail("Lefou exige race_choices.deformities com 2 pericias em modo strict.");
  }
  if (resolved.length < 2) {
    warnings.push("lefeu deformities were auto-selected");
  }
  const race = new mod.Lefeu(selectTopAttributes(attributes, 3));
  race.addDeformities(finalDeformities);
  return ok({
    race,
    appliedChoices: {
      deformities: finalDeformities,
    },
  });
}

function makeRace(raceName, attributes, buildChoices, strict, warnings) {
  const normalized = normalize(raceName);
  const raceChoices = isObject(buildChoices?.race_choices) ? buildChoices.race_choices : {};

  switch (normalized) {
    case "humano":
    case "human":
      return makeHumanRace(attributes, raceChoices, strict, warnings);
    case "anao":
    case "dwarf":
      return ok({ race: new mod.Dwarf(), appliedChoices: {} });
    case "dahllan":
      return ok({ race: new mod.Dahllan(), appliedChoices: {} });
    case "elfo":
    case "elf":
      return ok({ race: new mod.Elf(), appliedChoices: {} });
    case "goblin":
      return ok({ race: new mod.Goblin(), appliedChoices: {} });
    case "minotauro":
    case "minotaur":
      return ok({ race: new mod.Minotaur(), appliedChoices: {} });
    case "lefou":
    case "lefeu":
      return makeLefeuRace(attributes, raceChoices, strict, warnings);
    case "qareen":
      return ok({
        race: new mod.Qareen("water", mod.SpellName.arcaneArmor),
        appliedChoices: {
          heritage: "water",
          spell: mod.SpellName.arcaneArmor,
        },
      });
    default:
      return fail(`Raca '${raceName}' ainda nao esta suportada pela bridge automatica.`);
  }
}

function makeAcolyteOrigin(originChoices, strict, warnings) {
  const choices = isObject(originChoices) ? originChoices : {};
  const skill = choices.skill
    ? normalizeSkillName(choices.skill, [mod.SkillName.cure, mod.SkillName.religion, mod.SkillName.will])
    : strict
      ? null
      : mod.SkillName.cure;
  if (!skill) {
    return fail("Origem acolyte exige origin_choices.skill valida em modo strict.");
  }
  if (!choices.skill) {
    warnings.push("acolyte origin skill was auto-selected");
  }

  const generalPower = choices.general_power
    ? resolveGeneralPower(choices.general_power)
    : strict
      ? null
      : new mod.IronWill();
  if (!generalPower) {
    return fail("Origem acolyte exige origin_choices.general_power valida em modo strict.");
  }
  if (!choices.general_power) {
    warnings.push("acolyte origin general power was auto-selected");
  }

  return ok({
    origin: new mod.Acolyte([
      new mod.OriginBenefitGeneralPower(generalPower),
      new mod.OriginBenefitSkill(skill),
    ]),
    appliedChoices: {
      skill,
      general_power: generalPower.name || generalPower.constructor.name,
    },
  });
}

function makeAnimalsFriendOrigin(originChoices, strict, warnings) {
  const choices = isObject(originChoices) ? originChoices : {};
  const skill = choices.skill
    ? normalizeSkillName(choices.skill, [mod.SkillName.animalHandling, mod.SkillName.animalRide])
    : strict
      ? null
      : mod.SkillName.animalHandling;
  if (!skill) {
    return fail("Origem animals_friend exige origin_choices.skill valida em modo strict.");
  }
  if (!choices.skill) {
    warnings.push("animals_friend origin skill was auto-selected");
  }

  const companionSkill = choices.companion_skill
    ? normalizeSkillName(choices.companion_skill)
    : strict
      ? null
      : mod.SkillName.acrobatics;
  if (!companionSkill || companionSkill === mod.SkillName.fight || companionSkill === mod.SkillName.aim) {
    return fail("Origem animals_friend exige origin_choices.companion_skill valida (exceto fight/aim) em modo strict.");
  }
  if (!choices.companion_skill) {
    warnings.push("animals_friend companion skill was auto-selected");
  }

  const chosenAnimal = String(choices.animal || "").trim() || (strict ? "" : "dog");
  if (!chosenAnimal) {
    return fail("Origem animals_friend exige origin_choices.animal em modo strict.");
  }
  if (!choices.animal) {
    warnings.push("animals_friend companion animal was auto-selected");
  }

  return ok({
    origin: new mod.AnimalsFriend(
      [
        new mod.OriginBenefitSkill(skill),
        new mod.OriginBenefitOriginPower(new mod.SpecialFriend(companionSkill)),
      ],
      chosenAnimal,
    ),
    appliedChoices: {
      skill,
      companion_skill: companionSkill,
      animal: chosenAnimal,
    },
  });
}

function makeOrigin(originName, buildChoices, strict, warnings) {
  const normalized = normalize(originName);
  const originChoices = isObject(buildChoices?.origin_choices) ? buildChoices.origin_choices : {};

  switch (normalized) {
    case "acolyte":
    case "acolito":
      return makeAcolyteOrigin(originChoices, strict, warnings);
    case "animalsfriend":
    case "animals_friend":
    case "amigo dos animais":
    case "amigo_dos_animais":
      return makeAnimalsFriendOrigin(originChoices, strict, warnings);
    default:
      return fail(`Origem '${originName}' ainda nao esta suportada pela bridge automatica.`);
  }
}

function makeInitialEquipment(resolvedRole, buildChoices, strict, warnings) {
  const equipmentChoices = isObject(buildChoices?.equipment_choices) ? buildChoices.equipment_choices : {};
  const equipment = {
    simpleWeapon: new mod.Dagger(),
    money: 24,
  };

  if (strict && !isObject(buildChoices?.equipment_choices)) {
    return fail("equipment_choices e obrigatorio em modo strict.");
  }

  const simpleKey = equipmentChoices.simple_weapon;
  if (simpleKey) {
    const Ctor = EQUIPMENT_MAP[normalize(simpleKey)];
    if (!Ctor || !(Ctor === mod.Dagger)) {
      return fail(`equipment_choices.simple_weapon invalido: '${simpleKey}'.`);
    }
    equipment.simpleWeapon = new Ctor();
  } else if (!strict) {
    warnings.push("simple weapon was auto-selected");
  }

  const martialKey = equipmentChoices.martial_weapon;
  if (!MARTIAL_STARTER_ROLES.has(resolvedRole)) {
    if (martialKey) {
      return fail(`${resolvedRole} nao suporta equipment_choices.martial_weapon no equipamento inicial.`);
    }
  } else if (martialKey) {
    const Ctor = EQUIPMENT_MAP[normalize(martialKey)];
    if (!Ctor || !(Ctor === mod.LongSword)) {
      return fail(`equipment_choices.martial_weapon invalido: '${martialKey}'.`);
    }
    equipment.martialWeapon = new Ctor();
  } else if (!strict && mod.LongSword) {
    equipment.martialWeapon = new mod.LongSword();
    warnings.push("martial weapon was auto-selected");
  }

  if (resolvedRole !== "arcanista") {
    const armorKey = equipmentChoices.armor;
    if (armorKey) {
      const normalized = normalize(armorKey);
      if (normalized === "none") {
        // no armor
      } else {
        const Ctor = EQUIPMENT_MAP[normalized];
        if (!Ctor || Ctor !== mod.LeatherArmor) {
          return fail(`equipment_choices.armor invalido: '${armorKey}'.`);
        }
        equipment.armor = new Ctor();
      }
    } else if (!strict && mod.LeatherArmor) {
      equipment.armor = new mod.LeatherArmor();
      warnings.push("armor was auto-selected");
    }
  }

  if (typeof equipmentChoices.money === "number" && !Number.isNaN(equipmentChoices.money)) {
    equipment.money = Math.max(0, Math.floor(equipmentChoices.money));
  } else if (strict && Object.prototype.hasOwnProperty.call(equipmentChoices, "money")) {
    return fail("equipment_choices.money deve ser numerico.");
  }

  return ok({
    equipment,
    appliedChoices: {
      simple_weapon: equipment.simpleWeapon?.name || null,
      martial_weapon: equipment.martialWeapon?.name || null,
      armor: equipment.armor?.name || null,
      money: equipment.money,
    },
  });
}

function resolveIntelligenceSkills(attributes, buildChoices, strict, warnings) {
  const requested = Array.isArray(buildChoices?.intelligence_skill_choices)
    ? buildChoices.intelligence_skill_choices
    : [];
  const required = Math.max(0, Number(attributes.intelligence || 0));
  if (!Array.isArray(buildChoices?.intelligence_skill_choices)) {
    if (strict && required > 0) {
      return fail(`Informe ${required} pericias de inteligencia em modo strict.`);
    }
    if (required > 0) {
      warnings.push("intelligence skills were auto-selected as empty");
    }
    return ok({ values: [], autoSelected: required > 0 });
  }

  const resolved = [];
  for (const item of requested) {
    const skill = normalizeSkillName(item);
    if (!skill) {
      return fail(`intelligence_skill_choices contem pericia invalida '${item}'.`);
    }
    if (!resolved.includes(skill)) {
      resolved.push(skill);
    }
  }
  if (strict && resolved.length < required) {
    return fail(`Informe ${required} pericias de inteligencia validas em modo strict.`);
  }
  if (resolved.length < required) {
    warnings.push("intelligence skills list is shorter than intelligence modifier");
  }
  return ok({ values: resolved });
}

function buildSummary(serialized, extras) {
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
    requested_level: extras.requestedLevel,
    defense: sheet.defense?.total ?? null,
    life_points: sheet.lifePoints?.max ?? null,
    mana_points: sheet.manaPoints?.max ?? null,
    attributes: sheet.attributes || {},
    trained_skills: skills.filter((item) => item.trained).slice(0, 12),
    top_skills: skills.slice(0, 12),
    attacks: Array.isArray(serialized.attacks) ? serialized.attacks : [],
    build_steps: Array.isArray(sheet.buildSteps) ? sheet.buildSteps : [],
    serialized_character: serialized,
    warnings: extras.warnings,
    applied_choices: extras.appliedChoices,
  };
}

function main() {
  try {
    const rawInput = require("fs").readFileSync(0, "utf8");
    const payload = JSON.parse(rawInput || "{}");
    const buildChoices = isObject(payload.build_choices) ? payload.build_choices : {};
    const strict = normalize(payload.generation_mode) === "strict";
    const warnings = [];
    const attributes = normalizeAttributes(payload.attributes);

    const raceResult = makeRace(payload.race || "humano", attributes, buildChoices, strict, warnings);
    if (!raceResult.ok) {
      process.stdout.write(JSON.stringify({ success: false, error: raceResult.error }));
      return;
    }

    const roleResult = makeRole(payload.class_name || "guerreiro", buildChoices, strict, warnings, {
      attributes,
      raceName: payload.race || "humano",
      raceAppliedChoices: raceResult.appliedChoices,
    });
    if (!roleResult.ok) {
      process.stdout.write(JSON.stringify({ success: false, error: roleResult.error }));
      return;
    }

    const originResult = makeOrigin(payload.origin || "acolyte", buildChoices, strict, warnings);
    if (!originResult.ok) {
      process.stdout.write(JSON.stringify({ success: false, error: originResult.error }));
      return;
    }

    const intSkillResult = resolveIntelligenceSkills(attributes, buildChoices, strict, warnings);
    if (!intSkillResult.ok) {
      process.stdout.write(JSON.stringify({ success: false, error: intSkillResult.error }));
      return;
    }

    const equipmentResult = makeInitialEquipment(roleResult.resolvedName, buildChoices, strict, warnings);
    if (!equipmentResult.ok) {
      process.stdout.write(JSON.stringify({ success: false, error: equipmentResult.error }));
      return;
    }

    const builder = new mod.default();
    const sheet = builder
      .setInitialAttributes(attributes)
      .chooseRace(raceResult.race)
      .chooseRole(roleResult.role)
      .chooseOrigin(originResult.origin)
      .trainIntelligenceSkills(intSkillResult.values)
      .addInitialEquipment(equipmentResult.equipment)
      .build();
    const character = new mod.Character(sheet);
    const serialized = character.serialize();

    process.stdout.write(
      JSON.stringify({
        success: true,
        data: buildSummary(serialized, {
          requestedLevel: Number(payload.level || 1),
          warnings,
          appliedChoices: {
            ...roleResult.appliedChoices,
            intelligence_skill_choices: intSkillResult.values,
            race_choices: raceResult.appliedChoices,
            origin: payload.origin || "acolyte",
            origin_choices: originResult.appliedChoices,
            equipment_choices: equipmentResult.appliedChoices,
          },
        }),
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
