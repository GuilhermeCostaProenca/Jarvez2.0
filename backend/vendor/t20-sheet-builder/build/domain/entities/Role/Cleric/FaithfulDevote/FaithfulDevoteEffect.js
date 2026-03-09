"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.FaithfulDevoteEffect = void 0;
const Ability_1 = require("../../../Ability");
const ChangeGrantPowersCount_1 = require("../../../Action/ChangeGrantPowersCount");
class FaithfulDevoteEffect extends Ability_1.PassiveEffect {
    constructor(role, name) {
        super(name);
        this.description = FaithfulDevoteEffect.description[role];
    }
    apply(transaction) {
        transaction.run(new ChangeGrantPowersCount_1.ChangeGrantPowersCount({
            payload: {
                count: 2,
                source: this.source,
            },
            transaction,
        }));
    }
}
exports.FaithfulDevoteEffect = FaithfulDevoteEffect;
FaithfulDevoteEffect.description = {
    cleric: 'Você se torna devoto de um'
        + ' deus maior. Veja as regras de devotos na página 96.'
        + ' Ao contrário de devotos normais, você recebe dois'
        + ' poderes concedidos por se tornar devoto, em vez de'
        + ' apenas um.',
    druid: 'druidas (Allihanna, Megalokk'
        + ' ou Oceano). Veja as regras de devotos na página 96.'
        + ' Ao contrário de devotos normais, você recebe dois'
        + ' poderes concedidos por se tornar devoto, em vez de'
        + ' apenas um.',
};
