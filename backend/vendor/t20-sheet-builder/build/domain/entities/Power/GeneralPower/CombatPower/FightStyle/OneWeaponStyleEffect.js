"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.OneWeaponStyleEffect = void 0;
const GeneralPowerName_1 = require("../../GeneralPowerName");
const FightStyleEffect_1 = require("./FightStyleEffect");
class OneWeaponStyleEffect extends FightStyleEffect_1.FightStyleEffect {
    get description() {
        return OneWeaponStyleEffect.description;
    }
    constructor() {
        super(GeneralPowerName_1.GeneralPowerName.oneWeaponStyle);
    }
    canApply(character) {
        const wieldedItems = character.getWieldedItems();
        return wieldedItems.length === 1;
    }
}
exports.OneWeaponStyleEffect = OneWeaponStyleEffect;
OneWeaponStyleEffect.description = 'Se estiver usando uma arma corpo a corpo em uma das mãos '
    + ' e nada na outra, você recebe +2 na Defesa e nos testes de ataque com essa arma';
