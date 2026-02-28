"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.CharacterModifiers = exports.CharacterModifierName = void 0;
const Modifiers_1 = require("../Modifier/Modifiers");
var CharacterModifierName;
(function (CharacterModifierName) {
    CharacterModifierName["attack"] = "attack";
    CharacterModifierName["damage"] = "damage";
    CharacterModifierName["defense"] = "defense";
    CharacterModifierName["armorPenalty"] = "armorPenalty";
    CharacterModifierName["skillExceptAttack"] = "skillExceptAttack";
    CharacterModifierName["skill"] = "skill";
})(CharacterModifierName || (exports.CharacterModifierName = CharacterModifierName = {}));
class CharacterModifiers {
    constructor() {
        this.attack = new Modifiers_1.Modifiers();
        this.damage = new Modifiers_1.Modifiers();
        this.defense = new Modifiers_1.Modifiers();
        this.armorPenalty = new Modifiers_1.Modifiers();
        this.skillExceptAttack = new Modifiers_1.Modifiers();
        this.skill = new Modifiers_1.Modifiers();
    }
    serialize(sheet, context) {
        return {
            attack: this.attack.serialize(sheet, context),
            damage: this.damage.serialize(sheet, context),
            defense: this.defense.serialize(sheet, context),
            armorPenalty: this.armorPenalty.serialize(sheet, context),
            skillExceptAttack: this.skillExceptAttack.serialize(sheet, context),
            skill: this.skill.serialize(sheet, context),
        };
    }
}
exports.CharacterModifiers = CharacterModifiers;
