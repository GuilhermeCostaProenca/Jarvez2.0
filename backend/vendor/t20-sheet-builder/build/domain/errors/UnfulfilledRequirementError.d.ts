import { type RequirementInterface } from '../entities/Power/Power';
import { SheetBuilderError } from './SheetBuilderError';
export declare class UnfulfilledRequirementError extends SheetBuilderError {
    readonly requirement: RequirementInterface;
    name: string;
    constructor(requirement: RequirementInterface);
}
