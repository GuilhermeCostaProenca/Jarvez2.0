"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.OriginBenefitFactoryAnimalsFriend = void 0;
const Power_1 = require("../../../Power");
const OriginBenefitGeneralPower_1 = require("../OriginBenefitGeneralPower");
const OriginBenefitOriginPower_1 = require("../OriginBenefitOriginPower");
const OriginBenefitSkill_1 = require("../OriginBenefitSkill");
const OriginBenefitFactory_1 = require("./OriginBenefitFactory");
class OriginBenefitFactoryAnimalsFriend extends OriginBenefitFactory_1.OriginBenefitFactory {
    makeFromSerialized(serialized) {
        if (serialized.type === 'generalPowers') {
            return new OriginBenefitGeneralPower_1.OriginBenefitGeneralPower(Power_1.GeneralPowerFactory.make({ name: serialized.name }));
        }
        if (serialized.type === 'skills') {
            return new OriginBenefitSkill_1.OriginBenefitSkill(serialized.name);
        }
        return new OriginBenefitOriginPower_1.OriginBenefitOriginPower(new Power_1.SpecialFriend(serialized.skill));
    }
}
exports.OriginBenefitFactoryAnimalsFriend = OriginBenefitFactoryAnimalsFriend;
