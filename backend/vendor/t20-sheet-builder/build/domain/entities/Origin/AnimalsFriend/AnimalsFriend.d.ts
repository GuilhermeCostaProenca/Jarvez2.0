import type { Equipment } from '../../Inventory/Equipment/Equipment';
import type { EquipmentName } from '../../Inventory/Equipment/EquipmentName';
import type { GeneralPowerName } from '../../Power';
import { OriginPowerName } from '../../Power/OriginPower/OriginPowerName';
import { SkillName } from '../../Skill/SkillName';
import { Origin } from '../Origin';
import type { OriginBenefit } from '../OriginBenefit/OriginBenefit';
import { type SerializedOriginBenefitsAnimalsFriend } from '../OriginBenefit/SerializedOriginBenefit';
import { OriginName } from '../OriginName';
import { type SerializedAnimalsFriend } from '../SerializedOrigin';
export type AnimalsFriendEquipments = EquipmentName.hound | EquipmentName.horse | EquipmentName.pony | EquipmentName.trobo;
export declare class AnimalsFriend extends Origin<SerializedOriginBenefitsAnimalsFriend, SerializedAnimalsFriend> {
    chosenBenefits: Array<OriginBenefit<SerializedOriginBenefitsAnimalsFriend>>;
    readonly chosenAnimal: AnimalsFriendEquipments;
    static readonly originName = OriginName.animalsFriend;
    static equipments: string;
    static skills: SkillName[];
    static generalPowers: GeneralPowerName[];
    static originPower: OriginPowerName;
    readonly name = OriginName.animalsFriend;
    equipments: Equipment[];
    constructor(chosenBenefits: Array<OriginBenefit<SerializedOriginBenefitsAnimalsFriend>>, chosenAnimal: AnimalsFriendEquipments);
    serialize(): SerializedAnimalsFriend;
}
