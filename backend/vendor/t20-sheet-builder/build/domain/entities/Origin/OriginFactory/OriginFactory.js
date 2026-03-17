"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.OriginFactory = void 0;
const errors_1 = require("../../../errors");
const Power_1 = require("../../Power");
const Acolyte_1 = require("../Acolyte/Acolyte");
const AnimalsFriend_1 = require("../AnimalsFriend/AnimalsFriend");
const OriginBenefitFactoryAcolyte_1 = require("../OriginBenefit/OriginBenefitFactory/OriginBenefitFactoryAcolyte");
const OriginBenefitFactoryAnimalsFriend_1 = require("../OriginBenefit/OriginBenefitFactory/OriginBenefitFactoryAnimalsFriend");
const OriginBenefitGeneralPower_1 = require("../OriginBenefit/OriginBenefitGeneralPower");
const OriginBenefitOriginPower_1 = require("../OriginBenefit/OriginBenefitOriginPower");
const OriginBenefitSkill_1 = require("../OriginBenefit/OriginBenefitSkill");
const OriginName_1 = require("../OriginName");
class OriginFactory {
    static makeFromSerialized(serialized) {
        if (serialized.name === OriginName_1.OriginName.acolyte) {
            const benefitFactory = new OriginBenefitFactoryAcolyte_1.OriginBenefitFactoryAcolyte();
            const benefits = serialized.chosenBenefits.map(benefitFactory.makeFromSerialized);
            return new Acolyte_1.Acolyte(benefits);
        }
        if (serialized.name === OriginName_1.OriginName.animalsFriend) {
            const benefitFactory = new OriginBenefitFactoryAnimalsFriend_1.OriginBenefitFactoryAnimalsFriend();
            const benefits = serialized.chosenBenefits.map(benefitFactory.makeFromSerialized);
            return new AnimalsFriend_1.AnimalsFriend(benefits, serialized.chosenAnimal);
        }
        throw new errors_1.SheetBuilderError('UNKNOWN_ORIGIN');
    }
    static makeBenefitsFromSerialized(serialized) {
        if (serialized.type === 'generalPowers') {
            return new OriginBenefitGeneralPower_1.OriginBenefitGeneralPower(Power_1.GeneralPowerFactory.make({ name: serialized.name }));
        }
        if (serialized.type === 'skills') {
            return new OriginBenefitSkill_1.OriginBenefitSkill(serialized.name);
        }
        if (serialized.type === 'originPower') {
            if (serialized.name === Power_1.OriginPowerName.specialFriend) {
                return new OriginBenefitOriginPower_1.OriginBenefitOriginPower(new Power_1.SpecialFriend(serialized.skill));
            }
            return new OriginBenefitOriginPower_1.OriginBenefitOriginPower(Power_1.OriginPowerFactory.make({ power: serialized.name }));
        }
        throw new errors_1.SheetBuilderError('UNKNOWN_ORIGIN_BENEFIT_TYPE');
    }
}
exports.OriginFactory = OriginFactory;
