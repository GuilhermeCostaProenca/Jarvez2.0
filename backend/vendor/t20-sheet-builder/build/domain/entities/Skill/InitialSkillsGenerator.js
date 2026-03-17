"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.InitialSkillsGenerator = void 0;
const Skill_1 = require("./Skill");
const SkillName_1 = require("./SkillName");
class InitialSkillsGenerator {
    static generate() {
        return {
            acrobatics: new Skill_1.Skill({
                name: SkillName_1.SkillName.acrobatics,
                attribute: 'dexterity',
            }),
            acting: new Skill_1.Skill({
                name: SkillName_1.SkillName.acting,
                attribute: 'charisma',
            }),
            stealth: new Skill_1.Skill({
                name: SkillName_1.SkillName.stealth,
                attribute: 'dexterity',
            }),
            thievery: new Skill_1.Skill({
                name: SkillName_1.SkillName.thievery,
                attribute: 'dexterity',
            }),
            gambling: new Skill_1.Skill({
                name: SkillName_1.SkillName.gambling,
                attribute: 'charisma',
            }),
            piloting: new Skill_1.Skill({
                name: SkillName_1.SkillName.piloting,
                attribute: 'dexterity',
            }),
            animalHandling: new Skill_1.Skill({
                name: SkillName_1.SkillName.animalHandling,
                attribute: 'charisma',
            }),
            fight: new Skill_1.Skill({
                name: SkillName_1.SkillName.fight,
                attribute: 'strength',
            }),
            reflexes: new Skill_1.Skill({
                name: SkillName_1.SkillName.reflexes,
                attribute: 'dexterity',
            }),
            perception: new Skill_1.Skill({
                name: SkillName_1.SkillName.perception,
                attribute: 'wisdom',
            }),
            survival: new Skill_1.Skill({
                name: SkillName_1.SkillName.survival,
                attribute: 'wisdom',
            }),
            aim: new Skill_1.Skill({
                name: SkillName_1.SkillName.aim,
                attribute: 'dexterity',
            }),
            animalRide: new Skill_1.Skill({
                name: SkillName_1.SkillName.animalRide,
                attribute: 'dexterity',
            }),
            athletics: new Skill_1.Skill({
                name: SkillName_1.SkillName.athletics,
                attribute: 'strength',
            }),
            craft: new Skill_1.Skill({
                name: SkillName_1.SkillName.craft,
                attribute: 'intelligence',
            }),
            fortitude: new Skill_1.Skill({
                name: SkillName_1.SkillName.fortitude,
                attribute: 'constitution',
            }),
            initiative: new Skill_1.Skill({
                name: SkillName_1.SkillName.initiative,
                attribute: 'dexterity',
            }),
            intimidation: new Skill_1.Skill({
                name: SkillName_1.SkillName.intimidation,
                attribute: 'charisma',
            }),
            war: new Skill_1.Skill({
                name: SkillName_1.SkillName.war,
                attribute: 'intelligence',
            }),
            cheat: new Skill_1.Skill({
                name: SkillName_1.SkillName.cheat,
                attribute: 'charisma',
            }),
            diplomacy: new Skill_1.Skill({
                name: SkillName_1.SkillName.diplomacy,
                attribute: 'charisma',
            }),
            intuition: new Skill_1.Skill({
                name: SkillName_1.SkillName.intuition,
                attribute: 'wisdom',
            }),
            investigation: new Skill_1.Skill({
                name: SkillName_1.SkillName.investigation,
                attribute: 'intelligence',
            }),
            knowledge: new Skill_1.Skill({
                name: SkillName_1.SkillName.knowledge,
                attribute: 'intelligence',
            }),
            mysticism: new Skill_1.Skill({
                name: SkillName_1.SkillName.mysticism,
                attribute: 'intelligence',
            }),
            nobility: new Skill_1.Skill({
                name: SkillName_1.SkillName.nobility,
                attribute: 'intelligence',
            }),
            will: new Skill_1.Skill({
                name: SkillName_1.SkillName.will,
                attribute: 'wisdom',
            }),
            cure: new Skill_1.Skill({
                name: SkillName_1.SkillName.cure,
                attribute: 'wisdom',
            }),
            religion: new Skill_1.Skill({
                name: SkillName_1.SkillName.religion,
                attribute: 'wisdom',
            }),
        };
    }
}
exports.InitialSkillsGenerator = InitialSkillsGenerator;
