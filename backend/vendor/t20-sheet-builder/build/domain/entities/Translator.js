"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Translator = void 0;
const Capitalizer_1 = require("./Capitalizer");
const SpellCircle_1 = require("./Spell/SpellCircle");
class Translator {
    static getAttributeTranslation(attribute, capitalized = true) {
        const translatedAttribute = Translator.attributesTranslation[attribute];
        if (capitalized) {
            return Capitalizer_1.Capitalizer.capitalize(translatedAttribute);
        }
        return translatedAttribute;
    }
    static getRaceAbilityTranslation(ability) {
        return Translator.raceAbilitiesTranslation[ability];
    }
    static getSkillTranslation(skill) {
        return Translator.skillsTranslation[skill];
    }
    static getVisionTranslation(vision) {
        return Translator.visionsTranslation[vision];
    }
    static getRaceTranslation(race) {
        return Translator.racesTranslation[race];
    }
    static getRoleTranslation(role) {
        return Translator.rolesTranslation[role];
    }
    static getRoleAbilityTranslation(role) {
        return Translator.roleAbilitiesTranslation[role];
    }
    static getPowerTranslation(power) {
        return Translator.powersTranslation[power];
    }
    static getProficiencyTranslation(proficiency) {
        return Translator.proficienciesTranslation[proficiency];
    }
    static getSpellTranslation(spell) {
        return Translator.spellsTranslation[spell];
    }
    static getSpellCircleTranslation(circle) {
        return Translator.spellCirclesTranslation[circle];
    }
    static getEquipmentTranslation(equipment) {
        return Translator.equipmentsTranslation[equipment];
    }
    static getOriginTranslation(origin) {
        return Translator.originsTranslation[origin];
    }
    static getDamageTypeTranslation(damageType) {
        return Translator.damageTypesTranslation[damageType];
    }
    static getSpellTypeTranslation(spellType) {
        return Translator.spellTypesTranslation[spellType];
    }
    static getSpellSchoolTranslation(school) {
        return Translator.spellSchoolsTranslation[school];
    }
    static getSizeTranslation(size) {
        return Translator.sizesTranslation[size];
    }
    static getResistanceTranslation(resistance) {
        return Translator.resistancesTranslation[resistance];
    }
    static getTranslation(string) {
        return Translator.translation[string];
    }
}
exports.Translator = Translator;
Translator.attributesTranslation = {
    charisma: 'carisma',
    constitution: 'constituição',
    dexterity: 'destreza',
    intelligence: 'inteligência',
    strength: 'força',
    wisdom: 'sabedoria',
};
Translator.raceAbilitiesTranslation = {
    rockKnownledge: 'Conhecimento das Rochas',
    versatile: 'Versátil',
    slowAndAlways: 'Devagar e Sempre',
    hardAsRock: 'Duro como pedra',
    heredrimmTradition: 'Tradição Heredrimm',
    allihannaArmor: 'Armadura de Allihanna',
    plantsFriend: 'Amiga das Plantas',
    wildEmpathy: 'Empatia Selvagem',
    elvenSenses: 'Sentidos Élficos',
    gloriennGrace: 'Graça de Glórienn',
    magicBlood: 'Sangue Mágico',
    ingenious: 'Engenhoso',
    jointer: 'Espelunqueiro',
    slenderPlage: 'Peste Esguia',
    streetRat: 'Rato das Ruas	',
    deformity: 'Deformidade',
    sonOfTormenta: 'Filho da Tormenta',
    fearOfHeights: 'Medo de Altura',
    hornes: 'Chifres',
    nose: 'Faro',
    stiffLeather: 'Couro Rígido',
    desires: 'Desejos',
    elementalResistance: 'Resistência Elemental',
    mysticTattoo: 'Tatuagem Mística',
};
Translator.skillsTranslation = {
    acrobatics: 'Acrobacia',
    animalHandling: 'Adestramento',
    fight: 'Luta',
    perception: 'Percepção',
    reflexes: 'Reflexos',
    survival: 'Sobrevivência',
    aim: 'Pontaria',
    animalRide: 'Cavalgar',
    athletics: 'Atletismo',
    craft: 'Ofício',
    fortitude: 'Fortitude',
    initiative: 'Iniciativa',
    intimidation: 'Intimidação',
    war: 'Guerra',
    cheat: 'Enganação',
    diplomacy: 'Diplomacia',
    intuition: 'Intuição',
    investigation: 'Investigação',
    knowledge: 'Conhecimento',
    mysticism: 'Misticismo',
    nobility: 'Nobreza',
    will: 'Vontade',
    cure: 'Cura',
    religion: 'Religião',
    acting: 'Atuação',
    stealth: 'Furtividade',
    gambling: 'Jogatina',
    piloting: 'Pilotagem',
    thievery: 'Ladinagem',
};
Translator.powersTranslation = {
    dodge: 'Esquiva',
    oneWeaponStyle: 'Estilo de Uma Arma',
    archer: 'Arqueiro',
    medicine: 'Medicina',
    ironWill: 'Vontade de Ferro',
    churchMember: 'Membro da Igreja',
    specialFriend: 'Amigo Especial',
    shell: 'Carapaça',
    analyticMind: 'Mente Analítica',
    emptyMind: 'Mente Vazia',
    linWuTradition: 'Tradição de Lin-Wu',
};
Translator.visionsTranslation = {
    default: 'Visão padrão',
    penumbra: 'Visão na penumbra',
    dark: 'Visão no escuro',
};
Translator.racesTranslation = {
    dwarf: 'Anão',
    human: 'Humano',
    dahllan: 'Dahllan',
    elf: 'Elfo',
    goblin: 'Goblin',
    lefeu: 'Lefeu',
    minotaur: 'Minotauro',
    qareen: 'Qareen',
};
Translator.rolesTranslation = {
    warrior: 'Guerreiro',
    arcanist: 'Arcanista',
    barbarian: 'Bárbaro',
    buccaneer: 'Bucaneiro',
    bard: 'Bardo',
    ranger: 'Caçador',
    knight: 'Cavaleiro',
    cleric: 'Clérigo',
    druid: 'Druida',
    inventor: 'Inventor',
    rogue: 'Ladino',
    fighter: 'Lutador',
    noble: 'Nobre',
    paladin: 'Paladino',
};
Translator.proficienciesTranslation = {
    exotic: 'armas exóticas',
    fire: 'armas de fogo',
    heavyArmor: 'armaduras pesadas',
    lightArmor: 'armaduras leves',
    martial: 'armas marciais',
    shield: 'escudos',
    simple: 'armas simples',
};
Translator.roleAbilitiesTranslation = {
    specialAttack: 'Ataque Especial',
    warriorPower: 'Poder de Guerreiro',
    arcanistPath: 'Caminho do Arcanista',
    arcanistSpells: 'Magias (Arcanista)',
    arcanistSupernaturalLineage: 'Linhagem Sobrenatural',
    rage: 'Fúria',
    audacity: 'Audácia',
    bardSpells: 'Magias (Bardo)',
    preyMark: 'Marca da Presa',
    inspiration: 'Inspiração',
    tracker: 'Rastreador',
    honourCode: 'Código de Honra',
    bulwark: 'Baluarte',
    clericFaithfulDevote: 'Devoto Fiel (Clérigo)',
    clericSpells: 'Magias do Clérigo',
    druidFaithfulDevote: 'Devoto Fiel (Druida)',
    wildEmpathy: 'Empatia Selvagem',
    druidSpells: 'Magias (Druida)',
    ingenuity: 'Engenhosidade',
    prototype: 'Protótipo',
    sneakAttack: 'Ataque Furtivo',
    specialist: 'Especialista',
    fight: 'Briga',
    lightningStrike: 'Golpe Relâmpago',
    asset: 'Espólio',
    selfConfidence: 'Autoconfiança',
    blessed: 'Abençoado',
    divineBlow: 'Golpe Divino',
    heroCode: 'Código do Herói',
};
Translator.spellTypesTranslation = {
    arcane: 'Arcana',
    divine: 'Divina',
    universal: 'Universal',
};
Translator.spellsTranslation = {
    arcaneArmor: 'Armadura Arcana',
    illusoryDisguise: 'Disfarce Ilusório',
    mentalDagger: 'Adaga Mental',
    flamesExplosion: 'Explosão de Chamas',
    controlPlants: 'Controlar Plantas',
    cureWounds: 'Curar Ferimentos',
    divineProtection: 'Proteção Divina',
    faithShield: 'Escudo da Fé',
    magicWeapon: 'Arma Mágica',
};
Translator.spellCirclesTranslation = {
    [SpellCircle_1.SpellCircle.first]: 'primeiro',
    [SpellCircle_1.SpellCircle.second]: 'segundo',
};
Translator.originsTranslation = {
    acolyte: 'Acólito',
    animalsFriend: 'Amigo dos Animais',
};
Translator.equipmentsTranslation = {
    horse: 'Cavalo',
    hound: 'Cão de Caça',
    pony: 'Pônei',
    priestCostume: 'Trajes de Padre',
    sacredSymbol: 'Símbolo Sagrado',
    trobo: 'Trobo',
    backpack: 'Mochila',
    sleepingBag: 'Saco de Dormir',
    travelerCostume: 'Traje de Viajante',
    dagger: 'Adaga',
    club: 'Clava',
    longSword: 'Espada Longa',
    scythe: 'Gadanho',
    brunea: 'Brunea',
    leatherArmor: 'Armadura de Couro',
    studdedLeather: 'Couro Batido',
    chainMail: 'Cota de Malha',
    fullPlate: 'Armadura Completa',
    staff: 'Cajado',
    wand: 'Varinha',
    horns: 'Chifres',
    shortSword: 'Espada Curta',
    spear: 'Lança',
    mace: 'Maça',
    staffStick: 'Bordão',
    pike: 'Pique',
    baton: 'Tacape',
    assegai: 'Azagaia',
    lightCrossbow: 'Besta Leve',
    sling: 'Funda',
    shortbow: 'Arco Curto',
    hatchet: 'Machadinha',
    scimitar: 'Cimitarra',
    foil: 'Florete',
    battleAxe: 'Machado de Batalha',
    flail: 'Mangual',
    warHammer: 'Martelo de Guerra',
    pickaxe: 'Picareta',
    trident: 'Tridente',
    halberd: 'Alabarda',
    cutlass: 'Alfange',
    mountedSpear: 'Lança Montada',
    handAndaHalfSword: 'Montante',
    longBow: 'Arco Longo',
    heavyCrossbow: 'Besta Pesada',
    warAxe: 'Machado de Guerra',
    whip: 'Chicote',
    bastardSword: 'Espada Bastarda',
    katana: 'Katana',
    dwarfAxe: 'Machado Anão',
    chainofThorns: 'Corrente de Espinhos',
    tauricAxe: 'Machado Táurico',
    pistol: 'Pistola',
    musket: 'Mosquete',
    heavyShield: 'Escudo Pesado',
    lightShield: 'Escudo Leve',
    acid: 'Ácido',
    bomb: 'Bomba',
    loveElixir: 'Elixir do Amor',
    sickle: 'Foice',
};
Translator.arcanistPathsTranslation = {
    mage: 'Mago',
    sorcerer: 'Feiticeiro',
    wizard: 'Bruxo',
};
Translator.damageTypesTranslation = {
    acid: 'Ácido',
    cold: 'Frio',
    cutting: 'Cortante',
    darkness: 'Trevas',
    eletricity: 'Eletricidade',
    essence: 'Essência',
    fire: 'Fogo',
    impact: 'Impacto',
    light: 'Luz',
    piercing: 'Perfurante',
    psychic: 'Mental',
};
Translator.spellSchoolsTranslation = {
    abjuration: 'Abjuração',
    divination: 'Divinação',
    enchantment: 'Encantamento',
    evocation: 'Evocação',
    illusion: 'Ilusão',
    necromancy: 'Necromancia',
    summoning: 'Convocação',
    transmutation: 'Transmutação',
};
Translator.sizesTranslation = {
    colossal: 'Colossal',
    huge: 'Enorme',
    large: 'Grande',
    medium: 'Médio',
    small: 'Pequeno',
    tiny: 'Minúsculo',
};
Translator.deitiesTranslation = {
    aharadak: 'Aharadak',
    allihanna: 'Allihanna',
    azgher: 'Azgher',
    kallyadranoch: 'Kallyadranoch',
    khalmyr: 'Khalmyr',
    lena: 'Lena',
    linwuh: 'Lin-Wu',
    marah: 'Marah',
    megalokk: 'Megalokk',
    nimb: 'Nimb',
    sszzzaas: 'Sszzaas',
    tannatoh: 'Tanna-Toh',
    tenebra: 'Tenebra',
    thwor: 'Thwor',
    thyatis: 'Thyatis',
    valkaria: 'Valkaria',
};
Translator.resistancesTranslation = {
    tormenta: 'Tormenta',
    lefeu: 'Lefeu',
    acid: 'Ácido',
    cold: 'Frio',
    darkness: 'Trevas',
    electricity: 'Eletricidade',
    fire: 'Fogo',
    light: 'Luz',
};
Translator.equipmentImprovementsTranslation = {
    accurate: 'Certeira',
    cruel: 'Cruel',
    fit: 'Ajustada',
    reinforced: 'Reforçada',
};
Translator.translation = Object.assign(Object.assign(Object.assign(Object.assign(Object.assign(Object.assign(Object.assign(Object.assign(Object.assign(Object.assign(Object.assign(Object.assign(Object.assign(Object.assign(Object.assign(Object.assign(Object.assign(Object.assign(Object.assign(Object.assign(Object.assign(Object.assign({}, Translator.attributesTranslation), Translator.raceAbilitiesTranslation), Translator.skillsTranslation), Translator.powersTranslation), Translator.visionsTranslation), Translator.racesTranslation), Translator.rolesTranslation), Translator.proficienciesTranslation), Translator.roleAbilitiesTranslation), Translator.spellsTranslation), Translator.spellCirclesTranslation), Translator.originsTranslation), Translator.equipmentsTranslation), Translator.arcanistPathsTranslation), Translator.damageTypesTranslation), Translator.spellTypesTranslation), Translator.spellSchoolsTranslation), Translator.sizesTranslation), Translator.deitiesTranslation), Translator.resistancesTranslation), Translator.equipmentImprovementsTranslation), { default: 'Padrão' });
