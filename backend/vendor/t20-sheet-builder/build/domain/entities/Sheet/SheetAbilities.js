"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SheetAbilities = void 0;
class SheetAbilities {
    constructor(roleAbility = new Map(), raceAbility = new Map()) {
        this.roleAbility = roleAbility;
        this.raceAbility = raceAbility;
    }
    applyRoleAbility(ability, transaction, source) {
        ability.addToSheet(transaction, source);
        this.roleAbility.set(ability.name, ability);
    }
    applyRaceAbility(ability, transaction, source) {
        ability.addToSheet(transaction, source);
        this.raceAbility.set(ability.name, ability);
    }
    getRoleAbilities() {
        return this.roleAbility;
    }
    getRaceAbilities() {
        return this.raceAbility;
    }
}
exports.SheetAbilities = SheetAbilities;
