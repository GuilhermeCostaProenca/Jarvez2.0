import { type EquipmentImprovementCategory } from './EquipmentImprovementCategory';
import { type EquipmentImprovementName } from './EquipmentImprovementName';
export declare abstract class EquipmentImprovement {
    abstract name: EquipmentImprovementName;
    abstract description: string;
    abstract category: EquipmentImprovementCategory;
}
