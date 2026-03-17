"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DefensiveWeapon = void 0;
const Modifier_1 = require("../../../../Modifier");
const Weapon_1 = require("../Weapon");
class DefensiveWeapon extends Weapon_1.Weapon {
    get type() {
        return 'defensive';
    }
    onEquip(modifiers) {
        const modifier = new Modifier_1.FixedModifier(this.name, this.defenseBonus);
        this.modifierIndex = modifiers.defense.fixed.add(modifier);
    }
    onUnequip(modifiers) {
        if (this.modifierIndex !== undefined) {
            modifiers.defense.fixed.remove(this.modifierIndex);
        }
    }
}
exports.DefensiveWeapon = DefensiveWeapon;
