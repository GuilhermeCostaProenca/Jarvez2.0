import type { Equipment } from '../Inventory/Equipment/Equipment';
import { type OriginInterface } from './Origin';
import type { OriginBenefit } from './OriginBenefit/OriginBenefit';
import { type OriginBenefits } from './OriginBenefit/OriginBenefits';
import { OriginName } from './OriginName';
export declare class OriginFake implements OriginInterface {
    name: OriginName;
    equipments: Equipment[];
    chosenBenefits: OriginBenefit[];
    benefits: OriginBenefits;
    addToSheet: import("vitest").Mock<any, any>;
    serialize: import("vitest").Mock<any, any>;
}
