"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Sheet = void 0;
const Context_1 = require("../Context");
const SheetSkill_1 = require("../Skill/SheetSkill");
const SkillTotalCalculatorFactory_1 = require("../Skill/SkillTotalCalculatorFactory");
class Sheet {
    makeSkillTotalCalculator(context = new Context_1.OutOfGameContext()) {
        return SkillTotalCalculatorFactory_1.SkillTotalCalculatorFactory.make(this.getSheetAttributes().getValues(), this.getLevel(), context);
    }
    pushBuildSteps(...buildSteps) {
        this.buildSteps.push(...buildSteps);
    }
    getBuildSteps() {
        return this.buildSteps;
    }
    getLevel() {
        return this.level;
    }
    getSheetDevotion() {
        return this.sheetDevotion;
    }
    getSheetSize() {
        return this.sheetSize;
    }
    getSheetAbilities() {
        return this.sheetAbilities;
    }
    getSheetOrigin() {
        return this.sheetOrigin;
    }
    getSheetLifePoints() {
        return this.sheetLifePoints;
    }
    getMaxLifePoints() {
        const attributes = this.sheetAttributes.getValues();
        return this.sheetLifePoints.getMax(attributes, this.level);
    }
    getSheetManaPoints() {
        return this.sheetManaPoints;
    }
    getMaxManaPoints() {
        const attributes = this.sheetAttributes.getValues();
        return this.sheetManaPoints.getMax(attributes, this.level);
    }
    getSheetSkills() {
        return this.sheetSkills;
    }
    getSheetAttributes() {
        return this.sheetAttributes;
    }
    getSheetSpells() {
        return this.sheetSpells;
    }
    getSheetInventory() {
        return this.sheetInventory;
    }
    getSheetPowers() {
        return this.sheetPowers;
    }
    getSheetTriggeredEffects() {
        return this.sheetTriggeredEffects;
    }
    getSheetDefense() {
        return this.sheetDefense;
    }
    getSheetDefenseValue() {
        const attributes = this.sheetAttributes.getValues();
        const armorBonus = this.sheetInventory.getArmorBonus();
        const shieldBonus = this.sheetInventory.getShieldBonus();
        return this.sheetDefense.getTotal(attributes, armorBonus, shieldBonus);
    }
    getSheetVision() {
        return this.sheetVision;
    }
    getSheetRace() {
        return this.sheetRace;
    }
    getSheetRole() {
        return this.sheetRole;
    }
    getSheetProficiencies() {
        return this.sheetProficiencies;
    }
    getSheetDisplacement() {
        return this.sheetDisplacement;
    }
    getSheetResistences() {
        return this.sheetResistences;
    }
    getSkill(skillName) {
        const skill = this.getSheetSkills().getSkill(skillName);
        return this.makeSheetSkill(skill);
    }
    getSkills() {
        const skills = this.getSheetSkills().getSkills();
        // eslint-disable-next-line @typescript-eslint/consistent-type-assertions
        const sheetSkills = {};
        Object.entries(skills).forEach(([skillName, skill]) => {
            sheetSkills[skillName] = this.makeSheetSkill(skill);
        });
        return sheetSkills;
    }
    getSheetActivateableEffects() {
        return this.activateableEffects;
    }
    getActivateableEffects() {
        const map = this.activateableEffects.getEffects();
        return Array.from(map.values());
    }
    getActivateableEffect(name) {
        return this.activateableEffects.getEffect(name);
    }
    serialize(context = new Context_1.OutOfGameContext()) {
        const race = this.getSheetRace().getRace();
        const role = this.getSheetRole().getRole();
        const origin = this.getSheetOrigin().getOrigin();
        const powers = this.getSheetPowers();
        return {
            buildSteps: this.getBuildSteps().map(buildStep => buildStep.serialize()),
            level: this.getLevel(),
            initialAttributes: this.getSheetAttributes().getInitialAttributes(),
            displacement: this.getSheetDisplacement().getDisplacement(),
            attributes: this.getSheetAttributes().getValues(),
            defense: this.getSheetDefense().serialize(this, context),
            money: this.getSheetInventory().getMoney(),
            race: race ? race.serialize() : undefined,
            role: role ? role.serialize() : undefined,
            origin: origin ? origin.serialize() : undefined,
            lifePoints: this.getSheetLifePoints().serialize(this, context),
            manaPoints: this.getSheetManaPoints().serialize(this, context),
            equipments: this.getSheetInventory().serialize(),
            initialEquipment: this.getSheetInventory().serializeInitialEquipment(),
            generalPowers: powers.serializeGeneralPowers(),
            rolePowers: powers.serializeRolePowers(),
            originPowers: powers.serializeOriginPowers(),
            grantedPowers: powers.serializeGrantedPowers(),
            grantedPowersCount: this.getSheetDevotion().getGrantedPowerCount(),
            learnedCircles: this.getSheetSpells().serializeLearnedCircles(),
            proficiencies: this.getSheetProficiencies().getProficiencies(),
            skills: this.getSheetSkills().serialize(this, context),
            spells: this.getSheetSpells().serializeSpells(),
            tormentaPowersAttribute: this.getSheetAttributes().getTormentaPowersAttribute(),
            vision: this.getSheetVision().getVision(),
            devotion: this.getSheetDevotion().serialize(),
            resistencies: this.getSheetResistences().serialize(this, context),
        };
    }
    makeSheetSkill(skill) {
        return new SheetSkill_1.SheetSkill(skill, this.makeSkillTotalCalculator());
    }
}
exports.Sheet = Sheet;
