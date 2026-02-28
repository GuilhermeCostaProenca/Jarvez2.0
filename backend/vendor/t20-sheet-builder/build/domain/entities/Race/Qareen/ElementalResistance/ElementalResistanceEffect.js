"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ElementalResistanceEffect = void 0;
const Ability_1 = require("../../../Ability");
const AddResistance_1 = require("../../../Action/AddResistance");
const RaceAbilityName_1 = require("../../RaceAbilityName");
class ElementalResistanceEffect extends Ability_1.PassiveEffect {
    constructor(resistanceType) {
        super(RaceAbilityName_1.RaceAbilityName.elementalResistance);
        this.resistanceType = resistanceType;
        this.description = 'Conforme sua'
            + ' ascendência, você recebe redução 10 a um tipo de'
            + ' dano. Escolha uma: frio (qareen da água), eletricidade'
            + ' (do ar), fogo (do fogo), ácido (da terra), luz (da'
            + ' luz) ou trevas (qareen das trevas).';
    }
    apply(transaction) {
        transaction.run(new AddResistance_1.AddResistance({
            payload: {
                resistance: this.resistanceType,
                source: this.source,
                value: 10,
            },
            transaction,
        }));
    }
}
exports.ElementalResistanceEffect = ElementalResistanceEffect;
