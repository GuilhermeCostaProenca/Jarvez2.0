"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.OriginBenefitGeneralPower = void 0;
const PickGeneralPower_1 = require("../../Action/PickGeneralPower");
const SheetBuilderError_1 = require("../../../errors/SheetBuilderError");
const OriginBenefit_1 = require("./OriginBenefit");
class OriginBenefitGeneralPower extends OriginBenefit_1.OriginBenefit {
    constructor(power) {
        super();
        this.power = power;
        this.name = power.name;
    }
    serialize() {
        return {
            name: this.power.name,
            type: 'generalPowers',
        };
    }
    apply(transaction, source) {
        transaction.run(new PickGeneralPower_1.PickGeneralPower({
            payload: {
                power: this.power,
                source,
            },
            transaction,
        }));
    }
    validate(originBenefits) {
        if (!originBenefits.generalPowers.includes(this.power.name)) {
            throw new SheetBuilderError_1.SheetBuilderError('INVALID_ORIGIN_POWER');
        }
    }
}
exports.OriginBenefitGeneralPower = OriginBenefitGeneralPower;
