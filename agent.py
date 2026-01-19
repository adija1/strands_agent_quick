
"""
Strands Agent for Jira Issue Analysis and Solution Suggestions
This agent accepts questions about Jira issues and uses Atlassian MCP to search and suggest solutions.
"""

import json
from typing import Dict, List, Any
from strands import Agent, Tool, Context


class JiraIssueAgent:
    """Agent that analyzes Jira issues and suggests solutions"""
    
    def __init__(self, mcp_client):
        self.mcp_client = mcp_client
        self.agent = self._create_agent()
    
    def _create_agent(self) -> Agent:
        """Initialize the Strands agent with Atlassian MCP tools"""
        return Agent(
            name="JiraIssueAnalyzer",
            description="Analyzes Jira issues and provides solution suggestions",
            tools=[
                Tool(
                    name="search_jira_issues",
                    function=self.search_jira_issues,
                    description="Search for Jira issues using JQL or keywords"
                ),
                Tool(
                    name="get_issue_details",
                    function=self.get_issue_details,
                    description="Get detailed information about a specific Jira issue"
                ),
                Tool(
                    name="suggest_solutions",
                    function=self.suggest_solutions,
                    description="Analyze issue and suggest potential solutions"
                )
            ]
        )
    
    async def search_jira_issues(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search for Jira issues using the Atlassian MCP tool"""
        try:
            response = await self.mcp_client.call_tool(
                "atlassian_search_issues",
                {
                    "jql": query,
                    "max_results": max_results
                }
            )
            return response.get("issues", [])
        except Exception as e:
            return {"error": f"Failed to search issues: {str(e)}"}
    
    async def get_issue_details(self, issue_key: str) -> Dict[str, Any]:
        """Retrieve detailed information about a specific Jira issue"""
        try:
            response = await self.mcp_client.call_tool(
                "atlassian_get_issue",
                {"issue_key": issue_key}
            )
            return response
        except Exception as e:
            return {"error": f"Failed to get issue details: {str(e)}"}
    
    # Priority scoring
    async def suggest_solutions(self, issue_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Analyze issue and generate solution suggestions"""
        solutions = []
        issue_type = issue_data.get("fields", {}).get("issuetype", {}).get("name", "")
        priority = issue_data.get("fields", {}).get("priority", {}).get("name", "")
        description = issue_data.get("fields", {}).get("description", "")
        
        # Calculate priority score for solution ordering
        priority_scores = {
            "Highest": 5,
            "High": 4,
            "Medium": 3,
            "Low": 2,
            "Lowest": 1
        }
        
        
        if priority_scores.get(priority, 0) <= 3:
            solutions.append({
                "priority": "low",
                "suggestion": "This is a low priority issue. Consider addressing after critical items.",
                "action": "Schedule for next sprint"
            })
        else:
            solutions.append({
                "priority": "high",
                "suggestion": "This is a high priority issue requiring immediate attention.",
                "action": "Escalate to team lead and address immediately"
            })
        
        # Add type-specific solutions
        if issue_type == "Bug":
            solutions.append({
                "type": "debugging",
                "suggestion": "Review recent code changes and check error logs",
                "action": "Run diagnostic tests and reproduce the issue"
            })
        elif issue_type == "Story":
            solutions.append({
                "type": "implementation",
                "suggestion": "Break down into smaller tasks and estimate effort",
                "action": "Create subtasks and assign to team members"
            })
        
        return solutions
    
    async def process_question(self, question: str, context: Context) -> str:
        """Main entry point for processing questions about Jira issues"""
        # Extract issue key if present in question
        issue_key = self._extract_issue_key(question)
        
        if issue_key:
            # Get specific issue details
            issue_data = await self.get_issue_details(issue_key)
            if "error" not in issue_data:
                solutions = await self.suggest_solutions(issue_data)
                return self._format_response(issue_data, solutions)
            else:
                return f"Could not retrieve issue {issue_key}: {issue_data['error']}"
        else:
            # Search for relevant issues
            search_results = await self.search_jira_issues(question)
            if isinstance(search_results, dict) and "error" in search_results:
                return f"Search failed: {search_results['error']}"
            
            return self._format_search_results(search_results)
    
    def _extract_issue_key(self, text: str) -> str:
        """Extract Jira issue key from text (e.g., PROJ-123)"""
        import re
        match = re.search(r'\b[A-Z]+-\d+\b', text)
        return match.group(0) if match else None
    
    def _format_response(self, issue_data: Dict, solutions: List[Dict]) -> str:
        """Format issue details and solutions into readable response"""
        issue_key = issue_data.get("key", "Unknown")
        summary = issue_data.get("fields", {}).get("summary", "No summary")
        
        response = f"**Issue: {issue_key}**
"
        response += f"Summary: {summary}

"
        response += "**Suggested Solutions:**
"
        
        for idx, solution in enumerate(solutions, 1):
            response += f"{idx}. {solution.get('suggestion', 'No suggestion')}
"
            response += f"   Action: {solution.get('action', 'No action')}

"
        
        return response
    
    def _format_search_results(self, results: List[Dict]) -> str:
        """Format search results into readable response"""
        if not results:
            return "No issues found matching your query."
        
        response = f"Found {len(results)} issue(s):

"
        for issue in results[:5]:  # Limit to first 5
            key = issue.get("key", "Unknown")
            summary = issue.get("fields", {}).get("summary", "No summary")
            response += f"- {key}: {summary}
"
        
        return response


# Example usage
async def main():
    # Initialize MCP client (pseudo-code)
    mcp_client = AtlassianMCPClient(api_token="your_token")
    
    # Create agent
    agent = JiraIssueAgent(mcp_client)
    
    # Process questions
    question = "What's the status of SUP-129?"
    response = await agent.process_question(question, Context())
    print(response)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

