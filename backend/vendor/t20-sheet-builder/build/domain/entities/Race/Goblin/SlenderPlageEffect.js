"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SlenderPlageEffect = void 0;
const Ability_1 = require("../../Ability");
const ChangeSize_1 = require("../../Action/ChangeSize");
const Size_1 = require("../../Size");
const RaceAbilityName_1 = require("../RaceAbilityName");
class SlenderPlageEffect extends Ability_1.PassiveEffect {
    constructor() {
        super(RaceAbilityName_1.RaceAbilityName.slenderPlage);
        this.description = 'Seu tamanho é Pequeno,'
            + ' mas seu deslocamento se mantém 9m.'
            + ' Apesar de pequenos, goblins são rápidos.';
    }
    apply(transaction) {
        transaction.run(new ChangeSize_1.ChangeSize({
            payload: {
                size: Size_1.sizes.small,
                source: this.source,
            },
            transaction,
        }));
    }
}
exports.SlenderPlageEffect = SlenderPlageEffect;
