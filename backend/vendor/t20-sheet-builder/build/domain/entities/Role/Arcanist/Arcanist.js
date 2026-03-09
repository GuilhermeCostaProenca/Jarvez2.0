"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Arcanist = void 0;
const Level_1 = require("../../Sheet/Level");
const SkillName_1 = require("../../Skill/SkillName");
const Role_1 = require("../Role");
const RoleAbilitiesPerLevelFactory_1 = require("../RoleAbilitiesPerLevelFactory");
const RoleName_1 = require("../RoleName");
const ArcanistSpells_1 = require("./ArcanistSpells/ArcanistSpells");
class Arcanist extends Role_1.Role {
    static get startsWithArmor() {
        return false;
    }
    static get initialLifePoints() {
        return 8;
    }
    static get lifePointsPerLevel() {
        return 2;
    }
    static get manaPerLevel() {
        return 6;
    }
    constructor(chosenSkills, path, spells) {
        super(chosenSkills, Arcanist.selectSkillGroups);
        this.initialLifePoints = Arcanist.initialLifePoints;
        this.lifePointsPerLevel = Arcanist.lifePointsPerLevel;
        this.manaPerLevel = Arcanist.manaPerLevel;
        this.mandatorySkills = Arcanist.mandatorySkills;
        this.proficiencies = Arcanist.proficiencies;
        this.name = RoleName_1.RoleName.arcanist;
        this.initialSpells = 3;
        this.spellType = 'arcane';
        const arcanistSpells = new ArcanistSpells_1.ArcanistSpells(spells, path.spellLearnFrequency, path.spellsAttribute);
        this.abilitiesPerLevel = RoleAbilitiesPerLevelFactory_1.RoleAbilitiesPerLevelFactory.make({
            [Level_1.Level.one]: {
                arcanistSpells,
                arcanistPath: path,
            },
        });
    }
    getSpellsAttribute() {
        return this.abilitiesPerLevel[Level_1.Level.one].arcanistPath.spellsAttribute;
    }
    getSpellLearnFrequency() {
        return this.abilitiesPerLevel[Level_1.Level.one].arcanistPath.spellLearnFrequency;
    }
    getPath() {
        return this.abilitiesPerLevel[Level_1.Level.one].arcanistPath;
    }
    getInitialSpells() {
        return this.abilitiesPerLevel[Level_1.Level.one].arcanistSpells.effects.passive.default.spells;
    }
    serializeSpecific() {
        return {
            name: Arcanist.roleName,
            path: this.getPath().serializePath(),
            initialSpells: this.getInitialSpells().map(spell => spell.name),
        };
    }
}
exports.Arcanist = Arcanist;
Arcanist.roleName = RoleName_1.RoleName.arcanist;
Arcanist.selectSkillGroups = [
    {
        amount: 2,
        skills: [
            SkillName_1.SkillName.knowledge,
            SkillName_1.SkillName.diplomacy,
            SkillName_1.SkillName.cheat,
            SkillName_1.SkillName.war,
            SkillName_1.SkillName.initiative,
            SkillName_1.SkillName.intimidation,
            SkillName_1.SkillName.intuition,
            SkillName_1.SkillName.investigation,
            SkillName_1.SkillName.nobility,
            SkillName_1.SkillName.craft,
            SkillName_1.SkillName.perception,
        ],
    },
];
Arcanist.mandatorySkills = [SkillName_1.SkillName.mysticism, SkillName_1.SkillName.will];
Arcanist.proficiencies = [];
