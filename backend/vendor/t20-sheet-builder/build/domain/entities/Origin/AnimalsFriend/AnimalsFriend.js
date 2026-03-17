"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.AnimalsFriend = void 0;
const EquipmentAnimal_1 = require("../../Inventory/Equipment/EquipmentAnimal/EquipmentAnimal");
const OriginPowerName_1 = require("../../Power/OriginPower/OriginPowerName");
const SkillName_1 = require("../../Skill/SkillName");
const Origin_1 = require("../Origin");
const OriginName_1 = require("../OriginName");
class AnimalsFriend extends Origin_1.Origin {
    constructor(chosenBenefits, chosenAnimal) {
        super(chosenBenefits, {
            skills: AnimalsFriend.skills,
            generalPowers: AnimalsFriend.generalPowers,
            originPower: AnimalsFriend.originPower,
        });
        this.chosenBenefits = chosenBenefits;
        this.chosenAnimal = chosenAnimal;
        this.name = AnimalsFriend.originName;
        this.equipments = [new EquipmentAnimal_1.EquipmentAnimal(chosenAnimal)];
    }
    serialize() {
        return {
            name: this.name,
            chosenBenefits: this.serializeBenefits(),
            equipments: this.serializeEquipments(),
            chosenAnimal: this.chosenAnimal,
        };
    }
}
exports.AnimalsFriend = AnimalsFriend;
AnimalsFriend.originName = OriginName_1.OriginName.animalsFriend;
AnimalsFriend.equipments = 'Cão de caça, cavalo, pônei ou trobo (escolha um).';
AnimalsFriend.skills = [SkillName_1.SkillName.animalHandling, SkillName_1.SkillName.animalRide];
AnimalsFriend.generalPowers = [];
AnimalsFriend.originPower = OriginPowerName_1.OriginPowerName.specialFriend;
