import { EquipmentImprovementCategory } from '../../../EquipmentImprovement/EquipmentImprovementCategory';
import { DefensiveWeapon } from '../DefensiveWeapon';
export declare abstract class Shield extends DefensiveWeapon {
    readonly categoryForImprovement = EquipmentImprovementCategory.armorAndShield;
    get isWieldable(): boolean;
    constructor();
}
