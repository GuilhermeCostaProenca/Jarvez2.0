import { Equipment } from '../Equipment';
import { type EquipmentAlchemicCategory } from './EquipmentAlchemicCategory';
export declare abstract class EquipmentAlchemic extends Equipment {
    categoryForImprovement: null;
    abstract alchemicCategory: EquipmentAlchemicCategory;
    abstract description: string;
}
