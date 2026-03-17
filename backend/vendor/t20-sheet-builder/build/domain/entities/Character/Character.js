"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Character = void 0;
const Ability_1 = require("../Ability");
const Context_1 = require("../Context");
const Inventory_1 = require("../Inventory");
const Modifier_1 = require("../Modifier");
const FightStyle_1 = require("../Power/GeneralPower/CombatPower/FightStyle/FightStyle");
const Random_1 = require("../Random");
const SheetBuilder_1 = require("../Sheet/SheetBuilder");
const CharacterSkill_1 = require("../Skill/CharacterSkill");
const CharacterAttack_1 = require("./CharacterAttack");
const CharacterDefenseTriggeredEffect_1 = require("./CharacterDefenseTriggeredEffect");
const CharacterModifiers_1 = require("./CharacterModifiers");
class Character {
    static makeFromSerialized(serialized) {
        const sheet = SheetBuilder_1.SheetBuilder.makeFromSerialized(serialized.sheet);
        return new Character(sheet);
    }
    get maxWieldedItems() {
        return 2;
    }
    constructor(sheet, context = new Context_1.PreviewContext(sheet)) {
        this.sheet = sheet;
        this.context = context;
        this.modifiers = new CharacterModifiers_1.CharacterModifiers();
        this.selectDefaultFightStyle(sheet.getSheetPowers().getGeneralPowers());
    }
    attack(attack, random = new Random_1.Random()) {
        return attack.roll(random);
    }
    selectFightStyle(fightStyle) {
        const applied = fightStyle.applyModifiers(this.modifiers);
        this.fightStyle = applied;
    }
    unselectFightStyle() {
        var _a;
        (_a = this.fightStyle) === null || _a === void 0 ? void 0 : _a.removeModifiers(this.modifiers);
        this.fightStyle = undefined;
    }
    toggleEquipItem(name) {
        const inventory = this.sheet.getSheetInventory();
        inventory.toggleEquippedItem({
            maxWieldedItems: this.maxWieldedItems,
            modifiers: this.modifiers,
            name,
        });
    }
    getContextualModifierAppliableValue(modifier) {
        const calculator = new Modifier_1.ContextualModifierAppliableValueCalculator(this.getAttributes(), this.context, modifier);
        return modifier.getAppliableValue(calculator);
    }
    getAttributes() {
        const attributes = this.sheet.getSheetAttributes();
        return attributes.getValues();
    }
    getSkill(skillName) {
        const skill = this.makeCharacterSkill(this.sheet.getSkill(skillName), this.makeTotalCalculators());
        return skill;
    }
    getSkills() {
        // eslint-disable-next-line @typescript-eslint/consistent-type-assertions
        const skills = {};
        const totalCalculators = this.makeTotalCalculators();
        Object.entries(this.sheet.getSkills()).forEach(([skillName, skill]) => {
            skills[skillName] = this.makeCharacterSkill(skill, totalCalculators);
        });
        return skills;
    }
    getDefenseTriggeredEffects() {
        const effects = this.sheet.getSheetTriggeredEffects().getByEvent(Ability_1.TriggerEvent.defend);
        const characterDefenseEffects = new Map();
        for (const effect of effects.values()) {
            const defenseEffect = new CharacterDefenseTriggeredEffect_1.CharacterDefenseTriggeredEffect(effect, this.modifiers.defense);
            characterDefenseEffects.set(defenseEffect.effect.name, defenseEffect);
        }
        return characterDefenseEffects;
    }
    makeCharacterSkill(skill, totalCalculators) {
        return new CharacterSkill_1.CharacterSkill(skill, {
            skill: this.modifiers.skill.clone(),
            skillExceptAttack: this.modifiers.skillExceptAttack.clone(),
        }, this.makeSkillTriggeredEffects(), totalCalculators);
    }
    makeSkillTriggeredEffects() {
        return new Map([
            ...this.sheet.getSheetTriggeredEffects().getByEvent(Ability_1.TriggerEvent.skillTest),
            ...this.sheet.getSheetTriggeredEffects().getByEvent(Ability_1.TriggerEvent.skillTestExceptAttack),
        ]);
    }
    getAttacks() {
        const attacks = new Map();
        const inventory = this.sheet.getSheetInventory();
        const equipments = inventory.getEquipments();
        equipments.forEach(({ equipment }) => {
            if (equipment instanceof Inventory_1.OffensiveWeapon) {
                const typedEquipment = equipment;
                const attack = this.makeAttack(typedEquipment);
                attacks.set(typedEquipment.name, attack);
            }
        });
        return attacks;
    }
    getAttack(weaponName) {
        const inventory = this.sheet.getSheetInventory();
        const weapon = inventory.getEquipment(weaponName);
        if (!weapon || !(weapon.equipment instanceof Inventory_1.OffensiveWeapon)) {
            throw new Error('INVALID_EQUIPMENT');
        }
        const typedWeapon = weapon.equipment;
        return this.makeAttack(typedWeapon);
    }
    getWieldedItems() {
        const inventory = this.sheet.getSheetInventory();
        return inventory.getWieldedItems();
    }
    getFightStyle() {
        return this.fightStyle;
    }
    serialize() {
        var _a;
        const attacks = [];
        for (const attack of this.getAttacks().values()) {
            attacks.push(attack.serialize(this.sheet, this.context));
        }
        return {
            sheet: this.sheet.serialize(),
            modifiers: this.modifiers.serialize(this.sheet, this.context),
            fightStyle: (_a = this.fightStyle) === null || _a === void 0 ? void 0 : _a.fightStyle.serialize(),
            maxWieldedItems: this.maxWieldedItems,
            attacks,
        };
    }
    makeAttack(weapon) {
        const attackTriggeredEffects = this.sheet.getSheetTriggeredEffects().getByEvent(Ability_1.TriggerEvent.attack);
        const testTriggeredEffects = this.sheet.getSheetTriggeredEffects().getByEvent(Ability_1.TriggerEvent.skillTest);
        const effects = new Map([
            ...attackTriggeredEffects,
            ...testTriggeredEffects,
        ]);
        const attack = new CharacterAttack_1.CharacterAttack({
            weapon,
            skills: this.sheet.getSkills(),
            maxTotalCalculators: this.makeMaxTotalCalculators(),
            totalCalculators: this.makeTotalCalculators(),
            attributes: this.getAttributes(),
            modifiers: {
                damage: this.modifiers.damage,
                test: this.modifiers.attack,
            },
            triggeredEffects: effects,
        });
        return attack;
    }
    selectDefaultFightStyle(powers) {
        for (const power of powers.values()) {
            if (power instanceof FightStyle_1.FightStyle) {
                this.selectFightStyle(power);
                break;
            }
        }
    }
    makeMaxTotalCalculators() {
        return {
            fixedCalculator: this.makeFixedTotalCalculator(),
            perLevelCalculator: this.makePerLevelCalculator(),
        };
    }
    makeTotalCalculators() {
        return {
            contextCalculator: this.makeContextTotalCalculator(this.context),
            fixedCalculator: this.makeFixedTotalCalculator(),
            perLevelCalculator: this.makePerLevelCalculator(),
        };
    }
    makeContextTotalCalculator(context) {
        return new Modifier_1.ContextualModifiersListTotalCalculator(context, this.getAttributes());
    }
    makeFixedTotalCalculator() {
        return new Modifier_1.FixedModifiersListTotalCalculator(this.getAttributes());
    }
    makePerLevelCalculator() {
        return new Modifier_1.PerLevelModifiersListTotalCalculator(this.getAttributes(), this.sheet.getLevel());
    }
}
exports.Character = Character;
