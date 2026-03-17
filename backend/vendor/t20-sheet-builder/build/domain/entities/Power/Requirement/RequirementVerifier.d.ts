import type { Requirement } from './Requirement';
export declare abstract class RequirementVerifier {
    abstract verify(requirement: Requirement): boolean;
}
