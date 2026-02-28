"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.OriginBenefitOriginPower = void 0;
const PickOriginPower_1 = require("../../Action/PickOriginPower");
const SheetBuilderError_1 = require("../../../errors/SheetBuilderError");
const OriginBenefit_1 = require("./OriginBenefit");
class OriginBenefitOriginPower extends OriginBenefit_1.OriginBenefit {
    constructor(power) {
        super();
        this.power = power;
        this.name = power.name;
    }
    apply(transaction, source) {
        transaction.run(new PickOriginPower_1.PickOriginPower({
            payload: {
                power: this.power,
                source,
            },
            transaction,
        }));
    }
    validate(originBenefits) {
        if (originBenefits.originPower !== this.power.name) {
            throw new SheetBuilderError_1.SheetBuilderError('INVALID_ORIGIN_POWER');
        }
    }
    serialize() {
        return this.power.serialize();
    }
}
exports.OriginBenefitOriginPower = OriginBenefitOriginPower;
