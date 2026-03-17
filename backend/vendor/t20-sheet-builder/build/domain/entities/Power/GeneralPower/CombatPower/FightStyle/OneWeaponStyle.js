"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.OneWeaponStyle = void 0;
const AbilityEffects_1 = require("../../../../Ability/AbilityEffects");
const AbilityEffectsStatic_1 = require("../../../../Ability/AbilityEffectsStatic");
const CharacterAppliedFightStyle_1 = require("../../../../Character/CharacterAppliedFightStyle");
const ContextualModifier_1 = require("../../../../Modifier/ContextualModifier/ContextualModifier");
const Skill_1 = require("../../../../Skill");
const SkillRequirement_1 = require("../../../Requirement/SkillRequirement");
const GeneralPowerName_1 = require("../../GeneralPowerName");
const FightStyle_1 = require("./FightStyle");
const OneWeaponStyleEffect_1 = require("./OneWeaponStyleEffect");
class OneWeaponStyle extends FightStyle_1.FightStyle {
    constructor() {
        super(GeneralPowerName_1.GeneralPowerName.oneWeaponStyle);
        this.effects = new AbilityEffects_1.AbilityEffects({
            activateable: {
                default: new OneWeaponStyleEffect_1.OneWeaponStyleEffect(),
            },
        });
        this.condition = {
            description: 'Se estiver usando uma arma corpo a corpo em uma das mãos e nada na outra,',
            verify(context) {
                var _a;
                return ((_a = context.sheet) === null || _a === void 0 ? void 0 : _a.getSheetInventory().getWieldedItems().length) === 1;
            },
        };
        this.addRequirement(new SkillRequirement_1.SkillRequirement(Skill_1.SkillName.fight));
    }
    applyModifiers(modifiers) {
        const attackIndex = modifiers.attack.contextual.add(new ContextualModifier_1.ContextualModifier({
            source: GeneralPowerName_1.GeneralPowerName.oneWeaponStyle,
            value: 2,
            condition: this.condition,
        }));
        const defenseIndex = modifiers.defense.contextual.add(new ContextualModifier_1.ContextualModifier({
            source: GeneralPowerName_1.GeneralPowerName.oneWeaponStyle,
            value: 2,
            condition: this.condition,
        }));
        return new CharacterAppliedFightStyle_1.CharacterAppliedFightStyle(this, {
            attack: {
                contextual: [attackIndex],
            },
            defense: {
                contextual: [defenseIndex],
            },
        });
    }
    canActivate(character) {
        return character.getWieldedItems().length === 1;
    }
}
exports.OneWeaponStyle = OneWeaponStyle;
OneWeaponStyle.powerName = GeneralPowerName_1.GeneralPowerName.oneWeaponStyle;
OneWeaponStyle.effects = new AbilityEffectsStatic_1.AbilityEffectsStatic({
    activateable: {
        default: OneWeaponStyleEffect_1.OneWeaponStyleEffect,
    },
});
